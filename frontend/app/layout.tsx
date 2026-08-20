import "./styles.css";

export const metadata = { title: "VibeGraph", description: "Conversational semantic modelling" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
