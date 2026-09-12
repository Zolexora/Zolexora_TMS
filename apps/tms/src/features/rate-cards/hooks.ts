import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createRateCard } from './api';

export const useCreateRateCard = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createRateCard,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rate-cards'] });
    },
  });
};
