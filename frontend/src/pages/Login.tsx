import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, Lock, Eye, EyeOff } from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";

const Login: React.FC = () => {
  const { login } = useAuthStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const redirect = searchParams.get("redirect") || "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [touched, setTouched] = useState<{ email?: boolean; password?: boolean }>({});

  const validateField = (field: "email" | "password", value: string) => {
    const newErrors = { ...errors };
    if (field === "email") {
      if (!value) {
        newErrors.email = "Email address is required";
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        newErrors.email = "Please enter a valid email address";
      } else {
        delete newErrors.email;
      }
    }
    if (field === "password") {
      if (!value) {
        newErrors.password = "Password is required";
      } else if (value.length < 8) {
        newErrors.password = "Password must be at least 8 characters long";
      } else {
        delete newErrors.password;
      }
    }
    setErrors(newErrors);
  };

  const handleBlur = (field: "email" | "password") => {
    setTouched({ ...touched, [field]: true });
    if (field === "email") validateField("email", email);
    if (field === "password") validateField("password", password);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({ email: true, password: true });
    
    const hasEmailError = !email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    const hasPasswordError = !password || password.length < 8;

    if (hasEmailError || hasPasswordError) {
      validateField("email", email);
      validateField("password", password);
      return;
    }

    setIsLoading(true);
    setApiError(null);

    try {
      await login(email, password);
      navigate(redirect);
    } catch (err: any) {
      setApiError(err?.response?.data?.detail || err?.message || "Failed to sign in. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col lg:flex-row">
      <style>{`
        @keyframes float-slow-1 {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          50% { transform: translateY(-30px) translateX(15px); }
        }
        @keyframes float-slow-2 {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          50% { transform: translateY(20px) translateX(-20px); }
        }
        .animate-float-1 { animation: float-slow-1 18s ease-in-out infinite; }
        .animate-float-2 { animation: float-slow-2 22s ease-in-out infinite; }
        .grid-pattern {
          background-image: repeating-linear-gradient(0deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 40px),
                            repeating-linear-gradient(90deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 40px);
        }
      `}</style>

      {/* Left Panel - Desktop only */}
      <div className="hidden lg:flex lg:w-[55%] relative flex-col justify-between p-16 overflow-hidden bg-gradient-to-br from-slate-950 via-slate-950 to-blue-950/30 border-r border-white/5">
        <div className="absolute inset-0 grid-pattern pointer-events-none" />
        
        {/* Floating particles */}
        <div className="absolute top-1/4 left-1/3 w-72 h-72 rounded-full bg-blue-500/10 blur-[100px] animate-float-1 pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 rounded-full bg-emerald-500/5 blur-[120px] animate-float-2 pointer-events-none" />
        
        {/* Brand */}
        <div className="relative z-10">
          <Link to="/" className="text-2xl font-medium tracking-tight text-white">
            idea<span className="font-extrabold text-blue-500">forge</span>
          </Link>
        </div>

        {/* Hero Section */}
        <div className="relative z-10 space-y-6 max-w-lg my-auto">
          <h2 className="text-4xl font-extrabold leading-tight tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            Transform industry pain points into validated solutions
          </h2>
          <p className="text-slate-400 text-lg">
            An AI-powered startup discovery engine for founders, builders, and product leaders to find real problems worth solving.
          </p>
        </div>

        {/* Footer info */}
        <div className="relative z-10 text-xs text-slate-500">
          © {new Date().getFullYear()} IdeaForge. All rights reserved.
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-12 bg-slate-950">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="max-w-md w-full bg-slate-900/50 backdrop-blur-sm border border-white/5 p-8 rounded-2xl shadow-2xl space-y-6"
        >
          {/* Header */}
          <div className="space-y-1.5 text-center lg:text-left">
            <h1 className="text-2xl font-bold text-white tracking-tight">Welcome back</h1>
            <p className="text-slate-400 text-sm">Sign in to continue to IdeaForge</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Email address"
              type="email"
              placeholder="name@company.com"
              icon={Mail}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={() => handleBlur("email")}
              error={touched.email ? errors.email : undefined}
            />

            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                icon={Lock}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onBlur={() => handleBlur("password")}
                error={touched.password ? errors.password : undefined}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-[38px] text-slate-400 hover:text-white transition-colors"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {/* Error Message */}
            <AnimatePresence>
              {apiError && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs text-center"
                >
                  {apiError}
                </motion.div>
              )}
            </AnimatePresence>

            <Button type="submit" isLoading={isLoading} className="w-full">
              Sign in
            </Button>
          </form>

          {/* Switch page */}
          <div className="text-center text-sm text-slate-400 pt-2 border-t border-white/5">
            Don't have an account?{" "}
            <Link to="/register" className="text-blue-500 hover:text-blue-400 font-semibold transition-colors">
              Create an account
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Login;
