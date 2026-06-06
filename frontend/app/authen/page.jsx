"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { login as loginUser, register as registerUser } from "@/app/service/api/authen";
import { sessionStore } from "@/app/service/sessionStore";
import { useUser } from "@/app/context/UserContext";

function Field({
    label,
    id,
    name,
    type = "text",
    placeholder,
    autoComplete,
    value,
    onChange,
    required,
}) {
    return (
        <div className="space-y-2">
            <label htmlFor={id} className="block text-sm font-medium text-slate-200">
                {label}
            </label>
            <input
                id={id}
                name={name || id}
                type={type}
                placeholder={placeholder}
                autoComplete={autoComplete}
                value={value}
                onChange={onChange}
                required={required}
                className="w-full rounded-lg border border-zinc-700 bg-slate-950 px-3 py-2 text-slate-100 placeholder:text-slate-500 outline-none focus:border-zinc-500 focus:ring-2 focus:ring-slate-500/30"
            />
        </div>
    );
}

function Card({ title, subtitle, children }) {
    return (
        <section className="rounded-2xl border border-zinc-800 bg-black/40 p-6 shadow-xl">
            <header className="mb-6">
                <h2 className="text-2xl font-semibold tracking-tight text-slate-100">{title}</h2>
                {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
            </header>
            {children}
        </section>
    );
}

function ModeTabs({ mode, onChange }) {
    const base =
        "flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition-colors outline-none focus-visible:ring-2 focus-visible:ring-slate-500/30";
    const active = "bg-slate-950 text-slate-100 border border-zinc-700";
    const inactive = "bg-transparent text-slate-400 hover:text-slate-200";

    return (
        <div className="mb-6 rounded-xl border border-zinc-800 bg-black/30 p-1">
            <div className="flex gap-1">
                <button
                    type="button"
                    onClick={() => onChange("login")}
                    aria-pressed={mode === "login"}
                    className={`${base} ${mode === "login" ? active : inactive}`}
                >
                    Đăng nhập
                </button>
                <button
                    type="button"
                    onClick={() => onChange("register")}
                    aria-pressed={mode === "register"}
                    className={`${base} ${mode === "register" ? active : inactive}`}
                >
                    Đăng ký
                </button>
            </div>
        </div>
    );
}

export default function AuthenPage() {
    const router = useRouter();
    const { refreshUser, setUser } = useUser();
    const [mode, setMode] = useState("login");

    const [loginForm, setLoginForm] = useState({
        email: "",
        password: "",
    });

    const [loginLoading, setLoginLoading] = useState(false);
    const [loginError, setLoginError] = useState("");
    const [loginSuccess, setLoginSuccess] = useState(false);

    const [registerForm, setRegisterForm] = useState({
        firstname: "",
        lastname: "",
        email: "",
        phone: "",
        password: "",
    });
    const [registerLoading, setRegisterLoading] = useState(false);
    const [registerError, setRegisterError] = useState("");
    const [registerSuccess, setRegisterSuccess] = useState(null);

    const cardMeta = useMemo(() => {
        if (mode === "register") {
            return {
                title: "Tạo tài khoản",
                subtitle: "Điền thông tin để đăng ký tài khoản mới.",
            };
        }
        return {
            title: "Chào mừng quay lại",
            subtitle: "Đăng nhập để tiếp tục sử dụng hệ thống.",
        };
    }, [mode]);

    return (
        <div className="min-h-screen">
            <main className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-100">Authentication</h1>
                    <p className="mt-2 text-slate-400">Đăng nhập hoặc tạo tài khoản mới.</p>
                </div>

                <div className="mx-auto w-full max-w-xl">
                    <ModeTabs mode={mode} onChange={setMode} />

                    <Card title={cardMeta.title} subtitle={cardMeta.subtitle}>
                        {mode === "login" ? (
                            <form
                                className="space-y-4"
                                onSubmit={async (e) => {
                                    e.preventDefault();
                                    if (loginLoading) return;
                                    setLoginError("");
                                    setLoginSuccess(false);
                                    setLoginLoading(true);

                                    try {
                                        const result = await loginUser({
                                            email: loginForm.email.trim(),
                                            password: loginForm.password,
                                        });

                                        const accessToken = result?.accessToken;
                                        if (!accessToken) {
                                            throw new Error("Không nhận được accessToken");
                                        }

                                        sessionStore.setAccessToken(accessToken);

                                        const current = await refreshUser();
                                        setUser(current || null);

                                        if (current?.role === "ADMIN") {
                                            router.push("/admin");
                                        } else if (current?.role === "CUSTOMER") {
                                            router.push("/predict");
                                        } else {
                                            setLoginSuccess(true);
                                        }
                                    } catch (err) {
                                        const message =
                                            err?.response?.data?.message ||
                                            err?.message ||
                                            "Đăng nhập thất bại";
                                        setLoginError(message);
                                    } finally {
                                        setLoginLoading(false);
                                    }
                                }}
                            >
                                {loginError ? (
                                    <div className="rounded-lg border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                                        {loginError}
                                    </div>
                                ) : null}

                                {loginSuccess ? (
                                    <div className="rounded-lg border border-emerald-500 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                                        Đăng nhập thành công.
                                    </div>
                                ) : null}

                                <Field
                                    label="Email"
                                    id="email"
                                    name="email"
                                    type="email"
                                    placeholder="you@example.com"
                                    autoComplete="email"
                                    value={loginForm.email}
                                    onChange={(e) =>
                                        setLoginForm((prev) => ({ ...prev, email: e.target.value }))
                                    }
                                    required
                                />
                                <Field
                                    label="Password"
                                    id="password"
                                    name="password"
                                    type="password"
                                    placeholder="••••••••"
                                    autoComplete="current-password"
                                    value={loginForm.password}
                                    onChange={(e) =>
                                        setLoginForm((prev) => ({ ...prev, password: e.target.value }))
                                    }
                                    required
                                />

                                <button
                                    type="submit"
                                    disabled={loginLoading}
                                    className="mt-2 w-full rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
                                >
                                    {loginLoading ? "Đang đăng nhập..." : "Đăng nhập"}
                                </button>

                                <p className="pt-2 text-center text-sm text-slate-400">
                                    Chưa có tài khoản?{" "}
                                    <button
                                        type="button"
                                        onClick={() => setMode("register")}
                                        className="font-semibold text-slate-200 underline underline-offset-4"
                                    >
                                        Đăng ký
                                    </button>
                                </p>
                            </form>
                        ) : (
                            <form
                                className="space-y-4"
                                onSubmit={async (e) => {
                                    e.preventDefault();
                                    if (registerLoading) return;

                                    setRegisterError("");
                                    setRegisterSuccess(null);
                                    setRegisterLoading(true);

                                    try {
                                        const result = await registerUser({
                                            firstname: registerForm.firstname.trim(),
                                            lastname: registerForm.lastname.trim(),
                                            email: registerForm.email.trim(),
                                            phone: registerForm.phone.trim(),
                                            password: registerForm.password,
                                        });
                                        setRegisterSuccess(result);
                                    } catch (err) {
                                        const message =
                                            err?.response?.data?.message ||
                                            err?.message ||
                                            "Đăng ký thất bại";
                                        setRegisterError(message);
                                    } finally {
                                        setRegisterLoading(false);
                                    }
                                }}
                            >
                                {registerError ? (
                                    <div className="rounded-lg border border-red-500 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                                        {registerError}
                                    </div>
                                ) : null}

                                {registerSuccess ? (
                                    <div className="rounded-lg border border-emerald-500 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                                        Đăng ký thành công: {registerSuccess?.email}
                                    </div>
                                ) : null}

                                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                                    <Field
                                        label="Firstname"
                                        id="firstname"
                                        name="firstname"
                                        placeholder="Nguyễn"
                                        autoComplete="given-name"
                                        value={registerForm.firstname}
                                        onChange={(e) =>
                                            setRegisterForm((prev) => ({ ...prev, firstname: e.target.value }))
                                        }
                                        required
                                    />
                                    <Field
                                        label="Lastname"
                                        id="lastname"
                                        name="lastname"
                                        placeholder="Văn A"
                                        autoComplete="family-name"
                                        value={registerForm.lastname}
                                        onChange={(e) =>
                                            setRegisterForm((prev) => ({ ...prev, lastname: e.target.value }))
                                        }
                                        required
                                    />
                                </div>

                                <Field
                                    label="Email"
                                    id="registerEmail"
                                    name="email"
                                    type="email"
                                    placeholder="you@example.com"
                                    autoComplete="email"
                                    value={registerForm.email}
                                    onChange={(e) =>
                                        setRegisterForm((prev) => ({ ...prev, email: e.target.value }))
                                    }
                                    required
                                />

                                <Field
                                    label="Phone"
                                    id="phone"
                                    name="phone"
                                    type="tel"
                                    placeholder="0123 456 789"
                                    autoComplete="tel"
                                    value={registerForm.phone}
                                    onChange={(e) =>
                                        setRegisterForm((prev) => ({ ...prev, phone: e.target.value }))
                                    }
                                    required
                                />

                                <Field
                                    label="Password"
                                    id="registerPassword"
                                    name="password"
                                    type="password"
                                    placeholder="••••••••"
                                    autoComplete="new-password"
                                    value={registerForm.password}
                                    onChange={(e) =>
                                        setRegisterForm((prev) => ({ ...prev, password: e.target.value }))
                                    }
                                    required
                                />

                                <button
                                    type="submit"
                                    disabled={registerLoading}
                                    className="mt-2 w-full rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
                                >
                                    {registerLoading ? "Đang đăng ký..." : "Đăng ký"}
                                </button>

                                <p className="pt-2 text-center text-sm text-slate-400">
                                    Đã có tài khoản?{" "}
                                    <button
                                        type="button"
                                        onClick={() => setMode("login")}
                                        className="font-semibold text-slate-200 underline underline-offset-4"
                                    >
                                        Đăng nhập
                                    </button>
                                </p>
                            </form>
                        )}
                    </Card>
                </div>
            </main>
        </div>
    );
}
