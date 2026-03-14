/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: ["./src/**/*.{js,jsx,ts,tsx}"],
    theme: {
        extend: {
            colors: {
                cream: "#FDFBF7",
                paper: "#F6F1E6",
                brick: {
                    DEFAULT: "#9B2226",
                    hover: "#7F1D1F",
                    light: "#FEE2E2"
                },
                olive: {
                    DEFAULT: "#606C38",
                    light: "#FEFAE0"
                },
                terracotta: {
                    DEFAULT: "#BC6C25",
                    light: "#FEF3C7"
                },
                gold: "#DDA15E",
                ink: {
                    DEFAULT: "#1A1A1A",
                    light: "#4A4E69"
                },
                stone: "#8D99AE",
                // Legacy compatibility
                tomato: {
                    DEFAULT: "#9B2226",
                    hover: "#7F1D1F"
                },
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))"
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))"
                },
                destructive: {
                    DEFAULT: "hsl(var(--destructive))",
                    foreground: "hsl(var(--destructive-foreground))"
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))"
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))"
                },
                popover: {
                    DEFAULT: "hsl(var(--popover))",
                    foreground: "hsl(var(--popover-foreground))"
                },
                card: {
                    DEFAULT: "hsl(var(--card))",
                    foreground: "hsl(var(--card-foreground))"
                },
                chart: {
                    "1": "hsl(var(--chart-1))",
                    "2": "hsl(var(--chart-2))",
                    "3": "hsl(var(--chart-3))",
                    "4": "hsl(var(--chart-4))",
                    "5": "hsl(var(--chart-5))"
                }
            },
            fontFamily: {
                heading: ["Antonio", "sans-serif"],
                body: ["DM Sans", "sans-serif"],
                accent: ["Caveat", "cursive"],
                // Legacy
                serif: ["Antonio", "Georgia", "serif"],
                hand: ["Caveat", "cursive"],
                sans: ["DM Sans", "sans-serif"],
                ui: ["DM Sans", "sans-serif"]
            },
            borderRadius: {
                lg: "var(--radius)",
                md: "calc(var(--radius) - 2px)",
                sm: "calc(var(--radius) - 4px)",
                none: "0px"
            },
            keyframes: {
                "accordion-down": {
                    from: { height: "0" },
                    to: { height: "var(--radix-accordion-content-height)" }
                },
                "accordion-up": {
                    from: { height: "var(--radix-accordion-content-height)" },
                    to: { height: "0" }
                },
                "float": {
                    "0%, 100%": { transform: "translateY(0)" },
                    "50%": { transform: "translateY(-10px)" }
                },
                "spin-slow": {
                    from: { transform: "rotate(0deg)" },
                    to: { transform: "rotate(360deg)" }
                }
            },
            animation: {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
                "float": "float 3s ease-in-out infinite",
                "spin-slow": "spin-slow 8s linear infinite"
            }
        }
    },
    plugins: [require("tailwindcss-animate")]
};
