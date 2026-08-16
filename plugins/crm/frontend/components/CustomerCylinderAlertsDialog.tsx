import { Dialog } from "@systutor/shell/ui/dialog";
import { Alert } from "@systutor/shell/ui/alert";
import type { CustomerCylinderAlert } from "../../../logistics/frontend/api";

type CustomerCylinderAlertsDialogProps = {
  open: boolean;
  onClose: () => void;
  alerts: CustomerCylinderAlert[];
};

function severityTitle(severity: string) {
  if (severity === "CRITICAL") return "Crítico";
  if (severity === "ERROR") return "Error";
  if (severity === "WARNING") return "Advertencia";
  return severity;
}

export function CustomerCylinderAlertsDialog({ open, onClose, alerts }: CustomerCylinderAlertsDialogProps) {
  return (
    <Dialog open={open} title="Alertas de envases" onClose={onClose} maxWidthClassName="max-w-lg">
      <div className="space-y-3 text-sm text-foreground">
        {alerts.map((alert, i) => (
          <Alert
            key={`${alert.category}-${i}`}
            title={severityTitle(alert.severity)}
            className={
              alert.severity === "CRITICAL"
                ? "border-red-300 dark:border-red-700/50 bg-red-50 dark:bg-red-500/10 text-red-800 dark:text-red-100"
                : alert.severity === "WARNING"
                  ? "border-yellow-300 dark:border-yellow-700/50 bg-yellow-50 dark:bg-yellow-500/10 text-yellow-800 dark:text-yellow-100"
                  : undefined
            }
          >
            <div
              className={
                alert.severity === "CRITICAL"
                  ? "text-red-700 dark:text-red-50/90"
                  : alert.severity === "WARNING"
                    ? "text-yellow-700 dark:text-yellow-50/90"
                    : undefined
              }
            >
              {alert.message}
            </div>
          </Alert>
        ))}
      </div>
    </Dialog>
  );
}
