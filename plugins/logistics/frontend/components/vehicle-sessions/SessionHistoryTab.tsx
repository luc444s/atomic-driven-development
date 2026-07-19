import { Card, CardContent, CardHeader, CardTitle } from "../../../../../apps/web/src/shared/ui/card";

import type { SessionHistoryEntry } from "../../api";

type Props = {
  history: SessionHistoryEntry[];
};

export function SessionHistoryTab({ history }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Historial de jornada</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {history.length > 0 ? (
            history.map((entry) => (
              <div
                key={`${entry.occurred_at}-${entry.label}`}
                className="rounded-md border border-border p-3 text-sm"
              >
                <div className="font-medium">{entry.label}</div>
                <div className="text-muted-foreground">{new Date(entry.occurred_at).toLocaleString()}</div>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">Sin historial aún.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
