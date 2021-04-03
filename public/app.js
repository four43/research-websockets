class MyComponent extends HTMLElement {
	messages = [];

	initWs() {
		this.ws = new WebSocket(`ws://localhost:8000/thing/${this.thingId}`);
		this.ws.onopen = (event) => console.error(`[WS ${this.thingId}] Connected:`, event);
		this.ws.onclose = (event) => {
			console.error(`[WS ${this.thingId}]  close observed:`, event);
			window.setTimeout(this.initWs, 1000);
		};
		this.ws.onerror = (event) => console.error(`[WS ${this.thingId}] error observed:`, event);

		this.ws.onmessage = (message) => {
			this.messages.unshift(message);
			this.render();
		};
	}

	render() {
		const style = `<style>
			.container {
				width: 400px;
			}
			.message-list {
				height: 200px;
				overflow-x: hidden;
				overflow-y: scroll;
			}
			ul.message-list {
				list-style-type: none;
				margin: 0;
				padding: 0;
			}
		</style>`;
		let latestThing;
		let thingIdDisplay = this.thingId;
		if (this.thingId === "") {
			thingIdDisplay = "[all]";
		}

		let content = `<div class="container">`
		content += `<h1>Feed: <a href="//localhost:8000/thing/${this.thingId}" target="_blank">${thingIdDisplay}</a>`;

		if (this.thingId !== "" && this.messages[0]) {
			latestThing = JSON.parse(this.messages[0].data);
			content += ` <span>(${latestThing.thing})</span>`;
		}
		content += `</h1>`;

		content += `<ul class="message-list">`;
		for (let message of this.messages) {
			content += `<li><pre>${message.data}</pre></li>`;
		}
		content += `</ul>`;
		content += `</div>`;
		this.innerHTML = `${style}\n${content}`;
		if (this.thingId !== "" && this.messages[0]) {
			this.querySelector('h1 span').style.color = latestThing.color;
		}
	}

	connectedCallback() {
		this.thingId = this.getAttribute("thing-id")
		if (this.thingId === null) {
			this.thingId = "";
		}
		this.messages = [];
		this.render();
		this.initWs();
	}
}

customElements.define('thing-viewer', MyComponent);
