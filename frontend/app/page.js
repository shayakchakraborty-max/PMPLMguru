import { redirect } from "next/navigation";

// Root route — forwards everyone to the /auto launcher.
// Without this file, visiting https://<deploy>/ returns a 404.

export default function RootPage() {
  redirect("/auto");
}
