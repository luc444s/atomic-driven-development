import type { PluginFrontendContext, PluginFrontendRegistration } from "@systutor/sdk/frontend";
import { registerPlugin as purchaseRegister } from "../purchase/frontend/register";

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return purchaseRegister(ctx);
}
