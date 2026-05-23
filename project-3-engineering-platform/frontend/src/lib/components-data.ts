export interface ServiceInfo {
  id: string;
  name: string;
  fullName: string;
  color: string;
}

export interface FeatureInfo {
  id: string;
  name: string;
  ragQuery: string;
}

export const SERVICES: ServiceInfo[] = [
  { id: "kos",       name: "KOS",       fullName: "Key Operating System",                       color: "blue"   },
  { id: "icps",      name: "ICPS",      fullName: "IoT Certificate Provisioning Service",        color: "purple" },
  { id: "icms",      name: "ICMS",      fullName: "IoT Certificate Management Service",          color: "green"  },
  { id: "fpcs",      name: "FPCS",      fullName: "Factory Provisioning Crypto Service",         color: "teal"   },
  { id: "iam",       name: "IAM",       fullName: "Identity & Access Management",                color: "red"    },
  { id: "iads",      name: "IADS",      fullName: "IoT Asset Discovery Service",                 color: "yellow" },
  { id: "ilps",      name: "ILPS",      fullName: "Identity Lifecycle Provisioning Service",     color: "pink"   },
  { id: "igw",       name: "IGW",       fullName: "IoT Gateway",                                 color: "orange" },
  { id: "iotcommon", name: "iotcommon", fullName: "Shared DTOs & Security Library",              color: "gray"   },
];

// Add features per service here when ready.
// ragQuery = what gets sent to the RAG when user selects this feature.
export const FEATURES: Record<string, FeatureInfo[]> = {
  kos: [
    {
      id: "dlms",
      name: "DLMS Orders",
      ragQuery: "Explain the DLMS order creation flow in KOS — DAC and MICA order types, validation steps, and what happens after the order is saved",
    },
    // Add more KOS features here
  ],
  icps:      [], // Fill in later
  icms:      [],
  iads:      [],
  ilps:      [],
  igw:       [],
  iam:       [],
  fpcs:      [],
  iotcommon: [],
};

export function getComponentRagQuery(serviceId: string): string {
  const svc = SERVICES.find((s) => s.id === serviceId);
  if (!svc) return `Describe the ${serviceId} microservice`;
  return `Describe the ${svc.name} (${svc.fullName}) microservice in detail — its main responsibilities, key Java classes, important methods, and how it integrates with other services`;
}
