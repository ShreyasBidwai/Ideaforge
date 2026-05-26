import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, CheckCircle, Info, X } from "lucide-react";
import { useToastStore } from "../../stores/toastStore";

interface ToastProps {
  type: "success" | "error" | "info";
  message: string;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ type, message, onClose }) => {
  const icons = {
    success: <CheckCircle className="text-emerald-400 flex-shrink-0" size={18} />,
    error: <AlertCircle className="text-rose-400 flex-shrink-0" size={18} />,
    info: <Info className="text-blue-400 flex-shrink-0" size={18} />,
  };

  const bgColors = {
    success: "bg-emerald-950/80 border-emerald-500/20 text-emerald-100",
    error: "bg-rose-950/80 border-rose-500/20 text-rose-100",
    info: "bg-blue-950/80 border-blue-500/20 text-blue-100",
  };

  return (
    <div
      className={`
        flex items-start gap-3 p-4 rounded-xl border backdrop-blur-md shadow-2xl pointer-events-auto
        ${bgColors[type]}
      `}
    >
      {icons[type]}
      <p className="text-sm font-medium leading-tight flex-1 font-sans">
        {message}
      </p>
      <button
        onClick={onClose}
        className="text-slate-400 hover:text-white transition-colors"
      >
        <X size={16} />
      </button>
    </div>
  );
};

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, x: 50, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 50, scale: 0.9 }}
            transition={{ duration: 0.2 }}
          >
            <Toast
              type={toast.type}
              message={toast.message}
              onClose={() => removeToast(toast.id)}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default Toast;
