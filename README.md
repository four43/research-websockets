# Research Websockets

Is it symantic to use different protocols for the same endpoint? What does that look like? `GET http://.../resource/:id`
will give us point-in-time snapshot of that resource. What if we use `ws://.../resource/:id` to subscribe to updates?
How does that work?
