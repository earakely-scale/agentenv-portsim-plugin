import { renderTranscript as upstreamTranscript } from "../transcript.js?v=upstream";
import { renderLive } from "./live.js";

export * from "../transcript.js?v=upstream";

export function renderTranscript(root, rollout, task, opts) {
  return (rollout.live ? renderLive : upstreamTranscript)(root, rollout, task, opts);
}
