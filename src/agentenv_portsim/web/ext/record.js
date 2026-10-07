// ?record=1: what `agent-env portsim record` drives over the DevTools protocol, one frame at a time.
import { currentStage } from "./stage.js";

if (new URLSearchParams(location.search).get("record") === "1") {
  document.documentElement.classList.add("recording");
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const frames = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const deadline = performance.now() + 60e3;
  const until = async (ok) => {
    while (!ok()) {
      if (performance.now() > deadline) throw new Error(`the viewer did not load in 60 s: ${document.querySelector(".error")?.textContent ?? "no page error; is jsDelivr (three.js) reachable?"}`);
      await wait(100);
    }
  };
  /** The selected call in the middle of the transcript, so the news that arrives under it is on screen. */
  const center = () => {
    const call = document.querySelector("#transcript .call.sel");
    if (!call) return;
    const left = call.closest(".ro-left");
    const cover = left.querySelector(".ps-watch")?.offsetHeight || 0;
    left.scrollTop = call.offsetTop - left.offsetTop - cover - Math.max(0, (left.clientHeight - cover - call.offsetHeight) / 2);
  };
  window.portsim = {
    ready: (async () => {
      await until(() => currentStage() && document.querySelector("#transcript .msg:not(.skel)"));
      const { isLite } = await import("../scene.js");
      await until(() => isLite || currentStage().scene.el.dataset.post);
      await wait(3000);
      return { steps: document.querySelectorAll("#transcript .call[data-step]").length, horizon: Number(document.querySelector(".stage .range").max) };
    })(),
    async view(name) {
      const select = document.querySelector('.ov-tr [data-act="view"]');
      select.value = name;
      select.dispatchEvent(new Event("change"));
      await wait(1500);
    },
    async show(k) {
      document.querySelector(`#transcript .call[data-step="${k}"]`)?.click();
      center();
      await frames();
    },
    async time(h) {
      currentStage().setTime(h);
      center();
      await frames();
    },
  };
}
