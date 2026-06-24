import { useMutation } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { login } from "./api";
import { useAuthStore } from "./store";
import { ApiError } from "../../shared/api/client";
import { Alert } from "../../shared/ui/alert";
import { Button } from "../../shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../shared/ui/card";
import { Input } from "../../shared/ui/input";

type LocationState = {
  from?: {
    pathname?: string;
  };
};

export function LoginPage() {
  const token = useAuthStore((state) => state.token);
  const setSession = useAuthStore((state) => state.setSession);
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("ChangeMe123!");
  const from = (location.state as LocationState | null)?.from?.pathname ?? "/app/system";

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (response) => {
      setSession(response.access_token);
      navigate(from, { replace: true });
    },
  });

  useEffect(() => {
    if (token) {
      navigate("/app/system", { replace: true });
    }
  }, [navigate, token]);

  if (token) {
    return <Navigate replace to="/app/system" />;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loginMutation.mutate({ email, password });
  }

  const errorMessage =
    loginMutation.error instanceof ApiError
      ? loginMutation.error.message
      : loginMutation.error
        ? "No fue posible iniciar sesion."
        : null;

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-8">
      <Card className="w-full max-w-md border-slate-800 bg-slate-950/70 backdrop-blur">
        <CardHeader>
          <CardTitle>SYSTUTOR OSS</CardTitle>
          <CardDescription>
            Inicia sesion para acceder al shell del core y revisar el estado del sistema.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            {errorMessage ? <Alert title="Login fallido">{errorMessage}</Alert> : null}

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-200" htmlFor="email">
                Email
              </label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-200" htmlFor="password">
                Password
              </label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>

            <Button className="w-full" disabled={loginMutation.isPending} type="submit">
              {loginMutation.isPending ? "Ingresando..." : "Ingresar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
