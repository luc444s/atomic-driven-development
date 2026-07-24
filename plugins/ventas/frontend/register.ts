import type {
  PluginFrontendContext,
  PluginFrontendRegistration,
} from "@systutor/sdk/frontend";

import { registerPlugin as registerCotizacion } from "../cotizacion/frontend/register";

export function registerPlugin(ctx: PluginFrontendContext): PluginFrontendRegistration {
  return registerCotizacion(ctx);
}
