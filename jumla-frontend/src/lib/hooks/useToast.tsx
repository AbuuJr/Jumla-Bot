import { create } from 'zustand';


export type ToastType = 'success' | 'error' | 'warning' | 'info';


export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}


interface ToastStore {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  warning: (message: string) => void;
  info: (message: string) => void;
}


export const useToast = create<ToastStore>((set) => ({
  toasts: [],


  addToast: (toast) => {
    const id = Math.random().toString(36).substring(7);
    const newToast = { ...toast, id };


    set((state) => ({
      toasts: [...state.toasts, newToast],
    }));


    // Auto-remove after duration
    const duration = toast.duration || 5000;
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }));
    }, duration);
  },


  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },


  success: (message) => {
    set((state) => {
      const id = Math.random().toString(36).substring(7);
      const toast = { id, type: 'success' as ToastType, message };
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      }, 5000);
      return { toasts: [...state.toasts, toast] };
    });
  },


  error: (message) => {
    set((state) => {
      const id = Math.random().toString(36).substring(7);
      const toast = { id, type: 'error' as ToastType, message };
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      }, 5000);
      return { toasts: [...state.toasts, toast] };
    });
  },


  warning: (message) => {
    set((state) => {
      const id = Math.random().toString(36).substring(7);
      const toast = { id, type: 'warning' as ToastType, message };
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      }, 5000);
      return { toasts: [...state.toasts, toast] };
    });
  },


  info: (message) => {
    set((state) => {
      const id = Math.random().toString(36).substring(7);
      const toast = { id, type: 'info' as ToastType, message };
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      }, 5000);
      return { toasts: [...state.toasts, toast] };
    });
  },
}));



