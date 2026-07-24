export interface QuoteCommand {
  action: "cotizar" | "preview";
  dryRun: boolean;
  cliente: string | null;
  items: Array<{ cantidad: number; producto: string }>;
  fecha: string | null;
  hora: string | null;
  vehiculo: string | null;
  condiciones: string | null;
}
