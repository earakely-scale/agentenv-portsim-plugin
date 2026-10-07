import { createStage as upstreamStage } from "../stage.js?v=cargo-4";

export * from "../stage.js?v=cargo-4";

let latest = null;

export const currentStage = () => latest;

export function createStage(root, opts) {
  return (latest = upstreamStage(root, opts));
}
