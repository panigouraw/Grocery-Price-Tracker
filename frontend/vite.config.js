import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // GitHub Pages serves the site from /Grocery-Price-Tracker/
  base: command === "build" ? "/Grocery-Price-Tracker/" : "/",
}));
