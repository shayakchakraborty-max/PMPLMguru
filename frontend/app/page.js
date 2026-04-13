import { redirect } from "next/navigation";

// Root route — forwards everyone to the /auto launcher.
// Without this file, visiting https://<deploy>/ returns a 404 because
// the App Router has no page.js at the app/ root.

export default function RootPage() {
  redirect("/auto");
}
