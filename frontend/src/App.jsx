import { useEffect, useState } from "react";
import { API_BASE_URL } from "./config";

function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Backend returned an error");
        }

        return response.json();
      })
      .then((data) => {
        setBackendStatus(data.status);
      })
      .catch(() => {
        setBackendStatus("Offline");
        setError("Unable to connect to DQBH backend.");
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-6">
      <div className="w-full max-w-xl rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
        <div className="mb-8">
          <p className="mb-2 text-sm font-medium uppercase tracking-widest text-blue-400">
            DataQuest 3.0
          </p>

          <h1 className="text-4xl font-bold text-white">
            DQBH
          </h1>

          <p className="mt-3 text-slate-400">
            Intelligent Industrial Equipment Service Orchestration Platform
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950 p-5">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">
              Backend
            </span>

            <span className="font-semibold text-green-400">
              {backendStatus}
            </span>
          </div>

          {error && (
            <p className="mt-3 text-sm text-red-400">
              {error}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;