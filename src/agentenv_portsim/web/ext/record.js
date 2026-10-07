// ?record=1: what `agent-env portsim record` drives over the DevTools protocol, one frame at a time.
import { currentStage } from "./stage.js";

if (new URLSearchParams(location.search).get("record") === "1") {
  document.documentElement.classList.add("recording");
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const frames = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const until = async (ok) => {
    while (!ok()) await wait(100);
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
      const call = document.querySelector(`#transcript .call[data-step="${k}"]`);
      if (call) {
        call.click();
        const left = call.closest(".ro-left");
        left.scrollTop = call.offsetTop - left.offsetTop - (left.clientHeight - call.offsetHeight) / 2;
      }
      await frames();
    },
    async time(h) {
      currentStage().setTime(h);
      await frames();
    },
  };
}
