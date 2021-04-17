class DoodadViewer extends HTMLElement {
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
			h1 {
				margin-top: 0;
				color: #FFF;
				font-family: sans-serif;
			}
			h1 a {
				color: #FFF;
			}
			.container {
				width: 400px;
				background-color: #111;
				border-radius: 10px;
				border: 3px solid #000;
				box-shadow: 0 0 10px 1px #000000;
				margin: 10px;
				padding: 20px;
			}
			.message-list {
				height: 200px;
				overflow-x: hidden;
				overflow-y: scroll;
			}
			ul.message-list {
				color: #FFF;
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
		content += `<h1>Doodad: <a href="//localhost:8000/thing/${this.thingId}" target="_blank">${thingIdDisplay}</a>`;

		if (this.thingId !== "" && this.messages[0]) {
			latestThing = JSON.parse(this.messages[0].data);
			content += ` <span>(${latestThing.type})</span>`;
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
			this.querySelector('.container').style.boxShadow = `0 0 10px 1px ${latestThing.color}`
			this.querySelector('.container').style.borderColor = `${latestThing.color}`
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

customElements.define('doodad-viewer', DoodadViewer);
