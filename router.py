import asyncio
import json
from typing import Callable, Coroutine, Any, Optional, Union, Type, Dict, TYPE_CHECKING, \
    get_type_hints, get_args, List

from fastapi import params
from fastapi.datastructures import DefaultPlaceholder, Default
from fastapi.dependencies.models import Dependant
from fastapi.dependencies.utils import solve_dependencies
from fastapi.encoders import SetIntStr, DictIntStrAny
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.routing import APIRoute, run_endpoint_function, serialize_response, APIRouter
from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import ModelField
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from ws.content_type.abstract_content_type import AbstractContentType


class ContentAwareRouter(APIRouter):

    def __init__(self,
                 content_type_mappings: Dict[str, Type[AbstractContentType]] = None,
                 *args, **kwargs):
        self.content_type_mappings = content_type_mappings or {}
        route_class = configure_content_aware_route(
            content_type_mappings=self.content_type_mappings
        )
        super().__init__(route_class=route_class, *args, **kwargs)

    if not TYPE_CHECKING:  # pragma: no branch
        # Don't muck up our types since we're condensing here a lot.
        def add_api_route(self, path: str, endpoint: Callable[..., Any], **kwargs: Any) -> None:
            """
            Much like InferringRouter from fastapi_utils, gets response object and tries to infer content types bases
            on that.
            """
            if kwargs.get("response_model") is None:
                kwargs["response_model"] = get_type_hints(endpoint).get("return")

            if kwargs["response_model"] and kwargs.get("responses") is None:
                response_model = kwargs["response_model"]
                kwargs["responses"] = {
                    kwargs['status_code']: {
                        "description": endpoint.__doc__.strip() if endpoint.__doc__ is not None else None,
                        "model":       kwargs["response_model"],
                        "content":     {}
                    }
                }
                valid_response_section = kwargs["responses"][kwargs['status_code']]["content"]
                for mime_type, obj_interface in self.content_type_mappings.items():
                    try:
                        if issubclass(response_model, obj_interface):
                            docstring_example = obj_interface.to_example_docstring(response_model)

                            valid_response_section[mime_type] = {
                                "example": docstring_example
                            }
                    except TypeError:
                        pass

                    try:
                        if response_model.__origin__.__name__ == "list":
                            single_response = get_args(response_model)[0]
                            docstring_example = obj_interface.to_example_docstring(single_response)
                            valid_response_section[mime_type] = {
                                "example": f"[{docstring_example}]"
                            }
                    except AttributeError:
                        pass

            return super().add_api_route(path, endpoint, **kwargs)


def configure_content_aware_route(content_type_mappings: Dict[str, Type[AbstractContentType]]):
    class ContentAwareRoute(APIRoute):

        def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
            return get_request_handler(
                dependant=self.dependant,
                content_type_mappings=content_type_mappings,

                body_field=self.body_field,
                status_code=self.status_code,
                response_class=self.response_class,
                response_field=self.secure_cloned_response_field,
                response_model_include=self.response_model_include,
                response_model_exclude=self.response_model_exclude,
                response_model_by_alias=self.response_model_by_alias,
                response_model_exclude_unset=self.response_model_exclude_unset,
                response_model_exclude_defaults=self.response_model_exclude_defaults,
                response_model_exclude_none=self.response_model_exclude_none,
                dependency_overrides_provider=self.dependency_overrides_provider,
            )

    return ContentAwareRoute


def get_request_handler(
        dependant: Dependant,
        content_type_mappings: Dict[str, Type[AbstractContentType]],
        body_field: Optional[ModelField] = None,
        status_code: int = 200,
        response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
        response_field: Optional[ModelField] = None,
        response_model_include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
        response_model_exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        dependency_overrides_provider: Optional[Any] = None,
) -> Callable[[Request], Coroutine[Any, Any, Response]]:
    assert dependant.call is not None, "dependant.call must be a function"
    is_coroutine = asyncio.iscoroutinefunction(dependant.call)
    is_body_form = body_field and isinstance(body_field.field_info, params.Form)
    if isinstance(response_class, DefaultPlaceholder):
        actual_response_class: Type[Response] = response_class.value
    else:
        actual_response_class = response_class

    async def app(request: Request) -> Response:
        try:
            body = None
            if body_field:
                if is_body_form:
                    body = await request.form()
                else:
                    body_bytes = await request.body()
                    if body_bytes:
                        body = await request.json()
        except json.JSONDecodeError as e:
            raise RequestValidationError([ErrorWrapper(e, ("body", e.pos))], body=e.doc)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e
        solved_result = await solve_dependencies(
            request=request,
            dependant=dependant,
            body=body,
            dependency_overrides_provider=dependency_overrides_provider,
        )
        values, errors, background_tasks, sub_response, _ = solved_result
        if errors:
            raise RequestValidationError(errors, body=body)
        else:
            raw_response = await run_endpoint_function(
                dependant=dependant, values=values, is_coroutine=is_coroutine
            )

            if isinstance(raw_response, Response):
                if raw_response.background is None:
                    raw_response.background = background_tasks
                return raw_response

            accept = request.headers['accept']

            # Default functionality, application/json via serialize_response
            if accept == 'application/json':
                response_data = await serialize_response(
                    field=response_field,
                    response_content=raw_response,
                    include=response_model_include,
                    exclude=response_model_exclude,
                    by_alias=response_model_by_alias,
                    exclude_unset=response_model_exclude_unset,
                    exclude_defaults=response_model_exclude_defaults,
                    exclude_none=response_model_exclude_none,
                    is_coroutine=is_coroutine,
                )
                response = actual_response_class(
                    content=response_data,
                    status_code=status_code,
                    background=background_tasks,  # type: ignore # in Starlette
                )
                response.headers.raw.extend(sub_response.headers.raw)
                if sub_response.status_code:
                    response.status_code = sub_response.status_code
                return response

            try:
                content_type_mapping: Type[AbstractContentType] = content_type_mappings[accept]
                if isinstance(raw_response, content_type_mapping):
                    return Response(media_type=accept,
                                    content=content_type_mapping._to_method()(raw_response),
                                    status_code=status_code)
                raise HTTPException(status_code=406, detail=f"Unable to format content for Accept: {accept}")

            except KeyError:
                raise HTTPException(status_code=406, detail=f"Unable to format content for Accept: {accept}")

    return app
