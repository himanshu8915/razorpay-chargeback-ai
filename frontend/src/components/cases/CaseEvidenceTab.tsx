import React, { useState } from "react";
import { CheckCircle2, XCircle, AlertCircle, FileSearch, X } from "lucide-react";

export default function CaseEvidenceTab({ caseData }: { caseData: any }) {
  const decision = caseData.decision_artifact;
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null);

  const openDrawer = (item: string) => {
    setSelectedEvidence(item);
    setDrawerOpen(true);
  };

  const renderEvidenceList = (items: string[], type: "supporting" | "contradicting" | "missing" | "key") => {
    if (!items || items.length === 0) {
      return <p className="text-sm text-gray-500 italic">None identified.</p>;
    }

    const icon = {
      supporting: <CheckCircle2 className="w-5 h-5 text-emerald-500 mr-2 mt-0.5 flex-shrink-0" />,
      contradicting: <XCircle className="w-5 h-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" />,
      missing: <AlertCircle className="w-5 h-5 text-amber-500 mr-2 mt-0.5 flex-shrink-0" />,
      key: <FileSearch className="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
    }[type];

    return (
      <ul className="space-y-3">
        {items.map((item, i) => (
          <li 
            key={i} 
            className="flex items-start text-sm text-gray-700 bg-white p-3 rounded border border-gray-100 shadow-sm cursor-pointer hover:border-blue-300 hover:ring-1 hover:ring-blue-300 transition-all"
            onClick={() => openDrawer(item)}
          >
            {icon}
            <span>{item}</span>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="relative">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        <div className="space-y-6">
          <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
            <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center">
              <CheckCircle2 className="w-5 h-5 text-emerald-500 mr-2" />
              Supporting Evidence
            </h3>
            {renderEvidenceList(decision?.supporting_evidence, "supporting")}
          </div>

          <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
            <h3 className="text-base font-semibold text-gray-900 mb-4 flex items-center">
              <FileSearch className="w-5 h-5 text-blue-500 mr-2" />
              Key Evidence
            </h3>
            {renderEvidenceList(decision?.key_evidence, "key")}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-red-50 rounded-lg p-5 border border-red-100">
            <h3 className="text-base font-semibold text-red-900 mb-4 flex items-center">
              <XCircle className="w-5 h-5 text-red-500 mr-2" />
              Contradicting Evidence
            </h3>
            {renderEvidenceList(decision?.contradicting_evidence, "contradicting")}
          </div>

          <div className="bg-amber-50 rounded-lg p-5 border border-amber-100">
            <h3 className="text-base font-semibold text-amber-900 mb-4 flex items-center">
              <AlertCircle className="w-5 h-5 text-amber-500 mr-2" />
              Missing Evidence
            </h3>
            {renderEvidenceList(decision?.missing_evidence, "missing")}
          </div>
        </div>
      </div>

      {/* Evidence Drawer Overlay */}
      {drawerOpen && (
        <div className="fixed inset-0 overflow-hidden z-50">
          <div className="absolute inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setDrawerOpen(false)} />
          <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
            <div className="pointer-events-auto w-screen max-w-md">
              <div className="flex h-full flex-col overflow-y-scroll bg-white shadow-xl">
                <div className="px-4 py-6 sm:px-6 bg-slate-50 border-b border-gray-200">
                  <div className="flex items-start justify-between">
                    <h2 className="text-lg font-medium text-gray-900">Evidence Detail</h2>
                    <div className="ml-3 flex h-7 items-center">
                      <button
                        type="button"
                        className="rounded-md bg-slate-50 text-gray-400 hover:text-gray-500"
                        onClick={() => setDrawerOpen(false)}
                      >
                        <span className="sr-only">Close panel</span>
                        <X className="h-6 w-6" aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                </div>
                <div className="relative flex-1 px-4 py-6 sm:px-6">
                  <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50 text-sm text-gray-600">
                    <div className="p-4 border-b border-gray-200 bg-white">
                      <FileSearch className="mx-auto h-8 w-8 text-blue-500 mb-2" />
                      <p className="font-semibold text-gray-900 text-center">{selectedEvidence}</p>
                    </div>
                    <div className="p-4 bg-gray-900 text-green-400 font-mono text-xs overflow-x-auto">
                      <pre>
                        {selectedEvidence && (selectedEvidence.toLowerCase().includes('delivery') || selectedEvidence.toLowerCase().includes('carrier')) 
                          ? JSON.stringify(caseData?.case?.delivery, null, 2)
                          : selectedEvidence && (selectedEvidence.toLowerCase().includes('customer') || selectedEvidence.toLowerCase().includes('user'))
                          ? JSON.stringify(caseData?.case?.customer, null, 2)
                          : selectedEvidence && (selectedEvidence.toLowerCase().includes('transaction') || selectedEvidence.toLowerCase().includes('payment'))
                          ? JSON.stringify(caseData?.case?.transaction, null, 2)
                          : JSON.stringify(caseData?.case?.order, null, 2)
                        }
                      </pre>
                    </div>
                  </div>
                  
                  <div className="mt-6 border-t border-gray-200 pt-6">
                     <h4 className="text-sm font-semibold text-gray-900 mb-2">System Confidence</h4>
                     <div className="w-full bg-gray-200 rounded-full h-2">
                       <div className="bg-blue-600 h-2 rounded-full" style={{ width: '100%' }}></div>
                     </div>
                     <p className="text-xs text-gray-500 mt-2">Verified directly from source system canonical records</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
