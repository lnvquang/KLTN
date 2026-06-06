import AdminSidebar from "@/components/layouts/AdminSidebar";
import AdminTopbar from "@/components/layouts/AdminTopbar";

export const metadata = {
    title: "Admin | Big Five AI Dashboard",
};

export default function AdminLayout({ children }) {
    return (
        <div className="flex min-h-screen bg-black text-white">
            <AdminSidebar />

            <div className="flex-1">
                <AdminTopbar />

                <main className="p-8">{children}</main>
            </div>
        </div>
    );
}
