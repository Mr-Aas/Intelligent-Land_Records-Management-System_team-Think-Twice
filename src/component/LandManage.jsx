import { useMemo, useState } from "react";
import { Search } from "lucide-react";

const landLands = [
    {
        id: "UP_NAG_00123",
        khasraId: "Khasra/G0123",
        propertyId: "P728000000",
        owner: "Ramesh Kumar",
        location: "Mawana Tehsil",
        status: "Verified",
        confidenceScore: 98,
    },
    {
        id: "UP_NAG_00124",
        khasraId: "Khasra/G0124",
        propertyId: "P233000002",
        owner: "Suresh Sharma",
        location: "Meerut City",
        status: "Audit Pending",
        confidenceScore: 65,
    },
    {
        id: "UP_NAG_00125",
        khasraId: "Khasra/G0125",
        propertyId: "P455000003",
        owner: "Anita Verma",
        location: "Sardhana Tehsil",
        status: "Illegal/Disputed",
        confidenceScore: 42,
    },
    {
        id: "UP_NAG_00126",
        khasraId: "Khasra/G0126",
        propertyId: "P987000004",
        owner: "Mohit Singh",
        location: "Mawana Tehsil",
        status: "Verified",
        confidenceScore: 94,
    },
    {
        id: "UP_NAG_00127",
        khasraId: "Khasra/G0127",
        propertyId: "P111000005",
        owner: "Priya Gupta",
        location: "Meerut City",
        status: "Audit Pending",
        confidenceScore: 70,
    },
];

const filters = [
    { label: "All Lands", value: "All" },
    { label: "VERIFIED Lands", value: "Verified" },
    { label: "AUDIT PENDING Lands", value: "Audit Pending" },
    { label: "ILLEGAL/DISPUTED Lands", value: "Illegal/Disputed" },
];

function StatusBadge({ status }) {
    const statusStyles = {
        Verified: "bg-green-100 text-green-800 border-green-200",
        "Audit Pending": "bg-yellow-100 text-yellow-800 border-yellow-200",
        "Illegal/Disputed": "bg-red-100 text-red-800 border-red-200",
    };

    return (
        <span
            className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${statusStyles[status]}`}
        >
            {status}
        </span>
    );
}

export default function LandManage() {
    const [activeFilter, setActiveFilter] = useState("All");
    const [searchText, setSearchText] = useState("");
    const [selectedLand, setSelectedLand] = useState(null);

    const filteredLands = useMemo(() => {
        const search = searchText.trim().toLowerCase();

        return landLands.filter((Land) => {
            const matchesFilter =
                activeFilter === "All" || Land.status === activeFilter;

            const matchesSearch =
                !search ||
                Land.id.toLowerCase().includes(search) ||
                Land.khasraId.toLowerCase().includes(search) ||
                Land.propertyId.toLowerCase().includes(search) ||
                Land.owner.toLowerCase().includes(search) ||
                Land.location.toLowerCase().includes(search);

            return matchesFilter && matchesSearch;
        });
    }, [activeFilter, searchText]);

    return (
        <main className="min-h-screen bg-slate-50 p-4 pt-20 md:p-8 md:pt-24">
            <div className="mb-6 overflow-x-auto">
                <div className="flex min-w-max items-center gap-4">
                    <h2 className="whitespace-nowrap text-2xl font-bold text-slate-900">
                        Land Record Management
                    </h2>

                    <div className="flex flex-nowrap gap-2">
                        {filters.map((filter) => (
                            <button
                                key={filter.value}
                                onClick={() => setActiveFilter(filter.value)}
                                className={`whitespace-nowrap rounded-lg border px-4 py-2 text-sm font-bold transition-all ${activeFilter === filter.value
                                    ? "border-[#155e75] bg-[#155e75] text-white shadow-sm"
                                    : "border-[#155e75] bg-white text-slate-800 hover:bg-[#8ecae6]/40"
                                    }`}
                            >
                                {filter.label}
                            </button>
                        ))}
                    </div>

                    <div className="relative ml-auto shrink-0 pr-60">
                        <Search
                            size={18}
                            className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500"
                        />

                        <input
                            type="search"
                            value={searchText}
                            onChange={(event) => setSearchText(event.target.value)}
                            placeholder="Search Land Records"
                            className="w-full rounded-lg border border-gray-300 bg-white pl-9 py-2 text-sm focus:border-[#155e75] focus:ring-2 focus:ring-[#8ecae6] outline-none"
                        />
                    </div>
                </div>
            </div>

            <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-200 px-5 py-4">
                    <h3 className="text-xl font-bold text-slate-900">Land Records List</h3>
                    <p className="mt-1 text-sm text-slate-500">
                        Showing {filteredLands.length} Land
                        {filteredLands.length !== 1 ? "s" : ""}
                    </p>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full min-w-237.5 text-left">
                        <thead className="bg-slate-50 text-sm text-slate-700">
                            <tr>
                                <th className="px-5 py-4 font-bold">Land ID</th>
                                <th className="px-5 py-4 font-bold">Khasra/Gata ID</th>
                                <th className="px-5 py-4 font-bold">Property ID</th>
                                <th className="px-5 py-4 font-bold">Owner</th>
                                <th className="px-5 py-4 font-bold">Location</th>
                                <th className="px-5 py-4 font-bold">Status</th>
                                <th className="px-5 py-4 font-bold">Confidence</th>
                                <th className="px-5 py-4 font-bold">Action</th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-slate-200">
                            {filteredLands.map((Land) => (
                                <tr key={Land.id} className="hover:bg-[#8ecae6]/10">
                                    <td className="px-5 py-4 font-semibold text-slate-900">
                                        {Land.id}
                                    </td>
                                    <td className="px-5 py-4 text-slate-700">{Land.khasraId}</td>
                                    <td className="px-5 py-4 text-slate-700">{Land.propertyId}</td>
                                    <td className="px-5 py-4 text-slate-700">{Land.owner}</td>
                                    <td className="px-5 py-4 text-slate-700">{Land.location}</td>
                                    <td className="px-5 py-4">
                                        <StatusBadge status={Land.status} />
                                    </td>
                                    <td className="px-5 py-4 font-semibold text-slate-700">
                                        {Land.confidenceScore}%
                                    </td>
                                    <td className="px-5 py-4">
                                        <button
                                            onClick={() => setSelectedLand(Land)}
                                            className="font-semibold text-[#155e75] hover:underline"
                                        >
                                            View Details
                                        </button>
                                    </td>
                                </tr>
                            ))}

                            {filteredLands.length === 0 && (
                                <tr>
                                    <td
                                        colSpan="8"
                                        className="px-5 py-12 text-center text-slate-500"
                                    >
                                        No land Lands found for this filter or search.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </section>

            {selectedLand && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
                    <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
                        <div className="mb-5 flex items-center justify-between">
                            <h3 className="text-xl font-bold text-slate-900">
                                Land Details
                            </h3>
                            <button
                                onClick={() => setSelectedLand(null)}
                                className="rounded-md px-3 py-1 text-slate-500 hover:bg-slate-100"
                            >
                                Close
                            </button>
                        </div>

                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                            <p><strong>Land ID:</strong> {selectedLand.id}</p>
                            <p><strong>Khasra ID:</strong> {selectedLand.khasraId}</p>
                            <p><strong>Property ID:</strong> {selectedLand.propertyId}</p>
                            <p><strong>Owner:</strong> {selectedLand.owner}</p>
                            <p><strong>Location:</strong> {selectedLand.location}</p>
                            <p><strong>Confidence:</strong> {selectedLand.confidenceScore}%</p>
                            <div>
                                <strong>Status:</strong>{" "}
                                <StatusBadge status={selectedV.status} />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
}