import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, Lock, Eye, EyeOff, User } from "lucide-react";
import { useAuthStore } from "../stores/authStore";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";

const Register: React.FC = () => {
  const { register } = useAuthStore();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const [errors, setErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});
  const [touched, setTouched] = useState<{
    fullName?: boolean;
    email?: boolean;
    password?: boolean;
    confirmPassword?: boolean;
  }>({});

  const getPasswordStrength = (pwd: string) => {
    if (!pwd) return { score: 0, label: "" };
    if (pwd.length < 8) return { score: 1, label: "Weak" };
    
    let classes = 0;
    if (/[a-z]/.test(pwd)) classes++;
    if (/[A-Z]/.test(pwd)) classes++;
    if (/[0-9]/.test(pwd)) classes++;
    if (/[^a-zA-Z0-9]/.test(pwd)) classes++;

    if (classes >= 3) {
      return { score: 3, label: "Strong" };
    } else if (classes >= 2) {
      return { score: 2, label: "Medium" };
    }
    return { score: 1, label: "Weak" };
  };

  const validateField = (
    field: "fullName" | "email" | "password" | "confirmPassword",
    value: string
  ) => {
    setErrors((prev) => {
      const next = { ...prev };
      if (field === "fullName") {
        if (!value.trim()) {
          next.fullName = "Full name is required";
        } else {
          delete next.fullName;
        }
      }
      if (field === "email") {
        if (!value) {
          next.email = "Email address is required";
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          next.email = "Please enter a valid email address";
        } else {
          delete next.email;
        }
      }
      if (field === "password") {
        if (!value) {
          next.password = "Password is required";
        } else if (value.length < 8) {
          next.password = "Password must be at least 8 characters long";
        } else {
          delete next.password;
        }
        if (confirmPassword && value !== confirmPassword) {
          next.confirmPassword = "Passwords do not match";
        } else if (confirmPassword && value === confirmPassword) {
          delete next.confirmPassword;
        }
      }
      if (field === "confirmPassword") {
        if (!value) {
          next.confirmPassword = "Confirm password is required";
        } else if (value !== password) {
          next.confirmPassword = "Passwords do not match";
        } else {
          delete next.confirmPassword;
        }
      }
      return next;
    });
  };

  const handleBlur = (
    field: "fullName" | "email" | "password" | "confirmPassword"
  ) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    validateField(field, field === "fullName" ? fullName : field === "email" ? email : field === "password" ? password : confirmPassword);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({ fullName: true, email: true, password: true, confirmPassword: true });
    
    const newErrors: {
      fullName?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};

    if (!fullName.trim()) {
      newErrors.fullName = "Full name is required";
    }

    if (!email) {
      newErrors.email = "Email address is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 8) {
      newErrors.password = "Password must be at least 8 characters long";
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = "Confirm password is required";
    } else if (confirmPassword !== password) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);
    setApiError(null);

    try {
      await register(email, password, fullName);
      navigate("/");
    } catch (err: any) {
      setApiError(err?.response?.data?.detail || err?.message || "Failed to create account. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const strength = getPasswordStrength(password);
  const barColors = ["bg-transparent", "bg-rose-500", "bg-amber-500", "bg-emerald-500"];
  const textColors = ["text-slate-500", "text-rose-400", "text-amber-400", "text-emerald-400"];

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
            Start discovering validated startup ideas
          </h2>
          <p className="text-slate-400 text-lg">
            Create an account to gain access to industry pain points analysis, automated evaluation rubrics, and the structured workspace.
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
          className="max-w-md w-full bg-slate-900/50 backdrop-blur-sm border border-white/5 p-8 rounded-2xl shadow-2xl space-y-5"
        >
          {/* Header */}
          <div className="space-y-1.5 text-center lg:text-left">
            <h1 className="text-2xl font-bold text-white tracking-tight">Create your account</h1>
            <p className="text-slate-400 text-sm">Start discovering validated startup ideas</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              id="full-name"
              label="Full Name"
              type="text"
              placeholder="Alex Johnson"
              icon={User}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              onBlur={() => handleBlur("fullName")}
              error={touched.fullName ? errors.fullName : undefined}
            />

            <Input
              id="email"
              label="Email address"
              type="email"
              placeholder="name@company.com"
              icon={Mail}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={() => handleBlur("email")}
              error={touched.email ? errors.email : undefined}
            />

            <div className="space-y-1.5">
              <div className="relative">
                <Input
                  id="password"
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
                  data-testid="password-toggle"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-[38px] text-slate-400 hover:text-white transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {/* Password strength bar */}
              {password && (
                <div className="space-y-1.5 pt-1">
                  <div className="flex items-center justify-between text-[10px] uppercase font-bold tracking-wider">
                    <span className="text-slate-400">Password Strength</span>
                    <span className={textColors[strength.score]}>{strength.label}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-1.5 h-1">
                    <div className={`h-full rounded-full transition-all duration-300 ${strength.score >= 1 ? barColors[strength.score] : "bg-white/10"}`} />
                    <div className={`h-full rounded-full transition-all duration-300 ${strength.score >= 2 ? barColors[strength.score] : "bg-white/10"}`} />
                    <div className={`h-full rounded-full transition-all duration-300 ${strength.score >= 3 ? barColors[strength.score] : "bg-white/10"}`} />
                  </div>
                </div>
              )}
            </div>

            <div className="relative">
              <Input
                id="confirm-password"
                label="Confirm Password"
                type={showConfirmPassword ? "text" : "password"}
                placeholder="••••••••"
                icon={Lock}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                onBlur={() => handleBlur("confirmPassword")}
                error={touched.confirmPassword ? errors.confirmPassword : undefined}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3.5 top-[38px] text-slate-400 hover:text-white transition-colors"
                tabIndex={-1}
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
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
              Create account
            </Button>
          </form>

          {/* Switch page */}
          <div className="text-center text-sm text-slate-400 pt-2 border-t border-white/5">
            Already have an account?{" "}
            <Link to="/login" className="text-blue-500 hover:text-blue-400 font-semibold transition-colors">
              Sign in
            </Link>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Register;
