import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

type QueryKey = readonly (string | number)[];

interface CoreMutationOptions<TData, TVariables> {
  successMessage: string;
  onSuccess?: (data: TData, vars: TVariables) => void | Promise<void>;
  invalidate?: ((data: TData, vars: TVariables) => QueryKey[]) | QueryKey[];
  onError?: (error: Error, vars: TVariables) => void;
}

export function useCoreMutation<TData, TVariables = void>(
  mutationFn: (vars: TVariables) => Promise<TData>,
  options: CoreMutationOptions<TData, TVariables>,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: async (data, vars) => {
      toast.success(options.successMessage);
      await options.onSuccess?.(data, vars);
      if (options.invalidate) {
        const keys =
          typeof options.invalidate === "function"
            ? options.invalidate(data, vars)
            : options.invalidate;
        if (keys.length > 0) {
          await Promise.all(
            keys.map((key) => queryClient.invalidateQueries({ queryKey: key })),
          );
        }
      }
    },
    onError: (error, vars) => {
      if (options.onError) {
        options.onError(error as Error, vars);
      } else {
        toast.error(
          error instanceof Error ? error.message : "Error inesperado",
        );
      }
    },
  });
}
