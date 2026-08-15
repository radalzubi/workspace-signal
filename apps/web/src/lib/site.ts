export const site = {
  name: "Workspace Signal",
  domain: "workspacesignal.com",
  url: "https://workspacesignal.com",
  email: "hello@workspacesignal.com",
  tagline: "Smarter upgrades for better workspaces.",
  description:
    "Independent workspace guides, practical comparisons, and verified deal context for home offices and small workspaces.",
} as const;

export type GuideSection = {
  heading: string;
  paragraphs: string[];
  bullets?: string[];
};

export type Guide = {
  slug: string;
  title: string;
  description: string;
  category: string;
  intent: "Buying guide" | "Problem solving" | "Budget guide" | "Setup guide";
  readMinutes: number;
  updated: string;
  takeaways: string[];
  sections: GuideSection[];
};

export type ProductPick = {
  slug: string;
  name: string;
  brand: string;
  category: "Charging" | "Docking";
  price: number;
  observed: string;
  merchantUrl: string;
  bestFor: string;
  facts: string[];
  caution: string;
  publicProgramRate: number;
  estimatedCommissionIfApproved: number;
};

export const productPicks: ProductPick[] = [
  {
    slug: "anker-675-monitor-stand-dock",
    name: "Anker 675 USB-C Docking Station (12-in-1, Monitor Stand, Wireless)",
    brand: "Anker",
    category: "Docking",
    price: 249.99,
    observed: "August 16, 2026",
    merchantUrl: "https://www.anker.com/products/a8377",
    bestFor: "A single product that raises a monitor, expands laptop ports, charges a phone, and routes cables.",
    facts: ["12-in-1 dock and monitor stand", "Up to 100W host charging", "4K at 60Hz HDMI output", "10W maximum wireless charging pad"],
    caution: "Confirm monitor footprint, laptop USB-C capabilities, operating-system support, and the complete port requirements before buying.",
    publicProgramRate: 8,
    estimatedCommissionIfApproved: 20,
  },
  {
    slug: "anker-nano-13-in-1-dock",
    name: "Anker Nano Docking Station (13-in-1, Triple Display, Built-In Removable Hub)",
    brand: "Anker",
    category: "Docking",
    price: 149.99,
    observed: "August 16, 2026",
    merchantUrl: "https://www.anker.com/products/a83c3-13-in-1-docking-station-with-built-in-hub?variant=45906851856534",
    bestFor: "A hybrid desk-and-travel setup that benefits from a removable hub.",
    facts: ["13-in-1 dock with detachable 6-in-1 hub", "Up to 100W host charging", "10Gbps maximum data transfer", "HDMI, DisplayPort, card slots, audio and Gigabit Ethernet"],
    caution: "Display behavior depends on the laptop and operating system. Anker says the USB-C and USB-A ports do not output video, and Linux is not supported.",
    publicProgramRate: 8,
    estimatedCommissionIfApproved: 12,
  },
  {
    slug: "anker-nano-100w-charging-station",
    name: "Anker Nano Charging Station (7-in-1, 100W)",
    brand: "Anker",
    category: "Charging",
    price: 79.99,
    observed: "August 16, 2026",
    merchantUrl: "https://www.anker.com/products/a91c8-100w-7-in-1-charging-station?variant=45217869201558",
    bestFor: "A small desk that needs laptop-capable USB-C charging and AC outlets in one reachable station.",
    facts: ["Three AC outlets, three USB-C ports and one USB-A port", "Up to 100W from one USB-C port", "1.3-inch status display", "Compact 4.76 by 2.86-inch footprint"],
    caution: "USB output is shared across connected devices, so the 100W figure does not apply to every port simultaneously.",
    publicProgramRate: 8,
    estimatedCommissionIfApproved: 6.4,
  },
  {
    slug: "anker-525-charging-station",
    name: "Anker 525 Charging Station",
    brand: "Anker",
    category: "Charging",
    price: 39.99,
    observed: "August 16, 2026",
    merchantUrl: "https://www.anker.com/products/a91c0?variant=42089536422038",
    bestFor: "A lower-cost desk power hub for several everyday devices.",
    facts: ["Three AC outlets", "Two USB-C and two USB-A ports", "Up to 67W from one USB-C port", "4.61 by 2.52-inch footprint"],
    caution: "Power is divided when several USB ports are used; compare the multi-port output table with the devices you need to charge.",
    publicProgramRate: 8,
    estimatedCommissionIfApproved: 3.2,
  },
];

export const guides: Guide[] = [
  {
    slug: "monitor-arm-for-small-desk",
    title: "How to Choose a Monitor Arm for a Small Desk",
    description: "A practical fit checklist for reclaiming desk space without buying an arm that your desk cannot safely support.",
    category: "Monitor Arms",
    intent: "Buying guide",
    readMinutes: 6,
    updated: "August 15, 2026",
    takeaways: ["Check desk and monitor compatibility first", "Measure rear and wall clearance", "Prefer useful adjustability over maximum reach"],
    sections: [
      { heading: "Start with compatibility", paragraphs: ["A monitor arm is useful only when its clamp, weight range, and mounting pattern match your equipment. Record the monitor weight without its original stand, screen size, VESA pattern, and desktop thickness before comparing products."], bullets: ["Confirm that the desk edge can accept a clamp or grommet mount", "Check for a metal frame or cable tray beneath the mounting point", "Keep the monitor inside the manufacturer's published weight range"] },
      { heading: "Measure the space the arm needs", paragraphs: ["Small desks often sit against a wall. Some arms swing behind the desk when the screen is pulled forward, so a compact desk can still require several inches of rear clearance. Measure the desk depth, wall gap, and desired eye position."], bullets: ["Low-profile arms suit desks close to walls", "A tall pole can help stack screens without using extra depth", "Route cables with enough slack for the full movement range"] },
      { heading: "Choose the right adjustment style", paragraphs: ["Gas-spring arms move frequently and easily, while pole-mounted arms can be simpler and more stable for a screen that rarely changes position. The better choice depends on behavior, not the number of advertised adjustments."], bullets: ["Frequent sit-stand movement favors easy height adjustment", "A fixed work position may not justify a complex mechanism", "For two screens, compare total load and side-to-side width"] },
    ],
  },
  {
    slug: "cable-management-standing-desk",
    title: "Cable Management for a Standing Desk",
    description: "Build a cable route that moves safely from sitting to standing and keeps power off the floor.",
    category: "Cable Management",
    intent: "Problem solving",
    readMinutes: 6,
    updated: "August 15, 2026",
    takeaways: ["Mount the power strip to the moving desktop", "Test at maximum height", "Separate permanent and removable cables"],
    sections: [
      { heading: "Move the power source with the desk", paragraphs: ["The cleanest standing-desk layout usually mounts a surge protector beneath the desktop. Device cables then move with the desk, leaving one controlled power cable to travel to the wall."], bullets: ["Use mounting hardware appropriate for the desktop material", "Keep power bricks ventilated and supported", "Do not place strain on plugs or adapters"] },
      { heading: "Create one flexible path", paragraphs: ["Bundle the cable that travels from desk to wall in a flexible sleeve or articulated spine. Leave enough length for full height, but keep the excess controlled so it cannot catch on feet or furniture."], bullets: ["Raise the desk to its maximum position before final fastening", "Test every cable while raising and lowering the desk", "Keep loops away from lifting columns and crossbars"] },
      { heading: "Design for maintenance", paragraphs: ["A perfectly hidden system that takes an hour to open is not practical. Separate cables that rarely change from laptop chargers and accessories that are frequently replaced."], bullets: ["Label both ends of similar cables", "Use reusable ties instead of permanent zip ties", "Leave one accessible charging connection"] },
    ],
  },
  {
    slug: "home-office-upgrades-under-50",
    title: "Home Office Upgrades Under $50: What to Prioritize",
    description: "A budget framework for choosing small improvements that solve daily workspace problems.",
    category: "Budget Upgrades",
    intent: "Budget guide",
    readMinutes: 5,
    updated: "August 15, 2026",
    takeaways: ["Fix friction before adding decoration", "Spend on the most repeated problem", "Verify the current price before buying"],
    sections: [
      { heading: "Rank problems by frequency", paragraphs: ["A modest budget has more impact when it removes something irritating that happens every day. List recurring issues—poor lighting, loose cables, missing storage, awkward laptop height—and rank them by frequency."], bullets: ["Daily discomfort outranks an occasional inconvenience", "One complete fix is better than several partial fixes", "Measure before ordering organizers or mounts"] },
      { heading: "High-utility categories", paragraphs: ["Cable clips, a desk mat, task lighting, a laptop riser, and small storage can each improve a specific workflow. The best category depends on the workspace, and a low price is not evidence of value."], bullets: ["Lighting should reduce shadows on the actual work area", "Storage should keep frequent items reachable", "A laptop riser may require a separate keyboard and mouse"] },
      { heading: "Treat deals as context", paragraphs: ["A discount matters only when the product is suitable and the reference price is credible. Compare the current price with recent observations where available, then check return terms and the total delivered cost."], bullets: ["Do not buy solely because a percentage looks large", "Check whether required accessories raise the real cost", "Prefer a useful product at a fair price over an irrelevant clearance item"] },
    ],
  },
  {
    slug: "small-apartment-desk-setup",
    title: "Plan a Small-Apartment Desk Setup",
    description: "Use zones, vertical space, and careful measurements to create a workspace that can coexist with the rest of the room.",
    category: "Small Spaces",
    intent: "Setup guide",
    readMinutes: 7,
    updated: "August 15, 2026",
    takeaways: ["Measure the entire chair-and-desk footprint", "Use vertical space intentionally", "Make the workspace easy to reset"],
    sections: [
      { heading: "Measure movement, not just furniture", paragraphs: ["The desk footprint is only part of the space requirement. Include chair movement, drawer clearance, walking paths, doors, windows, and the distance needed to sit comfortably."], bullets: ["Mark the proposed footprint with removable tape", "Test the chair path before purchasing", "Avoid blocking ventilation or emergency access"] },
      { heading: "Assign three zones", paragraphs: ["Divide the setup into work, storage, and utility zones. The work zone holds the screen and input devices, storage holds supplies, and the utility zone manages power, charging, and cables."], bullets: ["Keep the center work zone visually quiet", "Move archives and rarely used items above or away from the desk", "Place charging where devices can be reached without crossing the work surface"] },
      { heading: "Plan the daily reset", paragraphs: ["In a multipurpose room, a workspace feels smaller when unfinished work spreads into the living area. Give every frequently used item a clear return location and make shutdown a short routine."], bullets: ["Use one tray for loose daily items", "Provide a hook or stand for headphones", "Keep one open surface for the next task"] },
    ],
  },
  {
    slug: "compact-keyboard-for-work",
    title: "Choosing a Compact Keyboard for Work",
    description: "Compare layout, key access, connectivity, and desk-space savings before changing keyboard size.",
    category: "Desk Technology",
    intent: "Buying guide",
    readMinutes: 6,
    updated: "August 15, 2026",
    takeaways: ["Choose layout before switch type", "Protect keys your workflow uses", "Account for connectivity and charging"],
    sections: [
      { heading: "Choose the layout around your work", paragraphs: ["Compact keyboards save horizontal space, but smaller layouts remove or layer keys. A tenkeyless layout retains dedicated navigation keys, while more compact layouts may move arrows and function keys."], bullets: ["Frequent spreadsheet work may justify a number pad", "Coding and editing benefit from predictable navigation keys", "Check the exact key map rather than relying on a percentage label"] },
      { heading: "Evaluate the complete input setup", paragraphs: ["A narrower keyboard can bring the mouse closer to the body, but height, wrist angle, and key feel still matter. Consider the keyboard together with the pointing device and chair position."], bullets: ["Check front-edge height", "Avoid assuming a wrist rest is always necessary", "Leave room for comfortable mouse movement"] },
      { heading: "Plan connectivity", paragraphs: ["Wireless convenience introduces battery and pairing considerations. Wired connections avoid charging but add another cable. Multi-device switching is valuable only when it matches a real workflow."], bullets: ["Confirm operating-system compatibility", "Check whether the required receiver is included", "Choose a charging connector that fits existing equipment"] },
    ],
  },
  {
    slug: "desk-storage-for-tiny-spaces",
    title: "Desk Storage Ideas for Tiny Spaces",
    description: "Store supplies by frequency and use overlooked vertical and under-desk areas without creating new clutter.",
    category: "Organization",
    intent: "Problem solving",
    readMinutes: 5,
    updated: "August 15, 2026",
    takeaways: ["Store by frequency of use", "Preserve knee and cable clearance", "Use containers with defined jobs"],
    sections: [
      { heading: "Audit what belongs at the desk", paragraphs: ["Storage cannot solve an inventory problem by itself. Remove duplicates, relocate occasional supplies, and keep only work that is active or frequently referenced near the desk."], bullets: ["Daily items belong within reach", "Weekly items can move to a shelf", "Archives should not consume prime desk space"] },
      { heading: "Use overlooked surfaces", paragraphs: ["Wall rails, shelves, monitor risers, and under-desk drawers add storage without occupying the central work surface. Every option must respect wall type, desk structure, and movement clearances."], bullets: ["Check knee clearance before adding an under-desk drawer", "Keep shelves clear of the monitor's movement path", "Do not overload temporary adhesive mounting"] },
      { heading: "Avoid container clutter", paragraphs: ["A collection of small organizers can become clutter in a different form. Assign each container a specific purpose and leave visible empty space so items can be returned quickly."], bullets: ["Prefer one divided tray over many loose cups", "Choose dimensions from actual items", "Review unused supplies periodically"] },
    ],
  },
  {
    slug: "laptop-stand-small-desk",
    title: "Laptop Stands for Small Desks: A Fit Guide",
    description: "Decide whether a riser, vertical stand, or portable stand fits your screen, storage, and input needs.",
    category: "Laptop Stands",
    intent: "Buying guide",
    readMinutes: 5,
    updated: "August 15, 2026",
    takeaways: ["Decide whether the laptop stays open or closed", "Include keyboard and mouse space", "Protect ventilation"],
    sections: [
      { heading: "Choose the operating mode", paragraphs: ["An open laptop stand raises the built-in screen; a vertical stand stores a closed laptop used with an external display. Those solve different problems, so decide how the computer will be used before comparing dimensions."], bullets: ["Open stands require space for a separate keyboard at ergonomic heights", "Closed operation requires compatible power and display behavior", "Portable stands trade some stability for packability"] },
      { heading: "Check physical fit", paragraphs: ["Compare the stand's supported width, weight, and adjustment range with the laptop. Ensure contact points do not cover vents and that the base will not conflict with a monitor stand or desk shelf."], bullets: ["Measure the usable desk depth", "Check whether hinges remain stable at the desired angle", "Use protective contact surfaces appropriate for the device finish"] },
      { heading: "Account for the full system", paragraphs: ["The stand may save little space if it requires a large keyboard, dock, and several adapters. Sketch the complete setup—including cable directions—before purchasing."], bullets: ["Place the dock where ports remain reachable", "Avoid tight bends at laptop connectors", "Reserve airflow around power adapters"] },
    ],
  },
  {
    slug: "desk-lighting-small-workspace",
    title: "Desk Lighting for a Small Workspace",
    description: "Improve task visibility while controlling glare, shadows, heat, and the amount of desk space a lamp consumes.",
    category: "Lighting",
    intent: "Buying guide",
    readMinutes: 6,
    updated: "August 15, 2026",
    takeaways: ["Light the task, not the screen", "Control glare from the user's position", "Choose a base that fits the available surface"],
    sections: [
      { heading: "Identify the task", paragraphs: ["Paper work, video calls, detailed making, and general computer use need different light placement. Start with the task area and the direction of existing daylight rather than choosing a lamp by appearance alone."], bullets: ["Place task light opposite the writing hand to reduce shadows", "Keep bright sources out of direct screen reflections", "Use ambient room light to reduce extreme contrast"] },
      { heading: "Choose the mounting style", paragraphs: ["A weighted base is flexible but consumes surface area. A clamp saves desk space but requires a compatible edge. Monitor-mounted lights preserve the surface but must fit the screen and viewing position."], bullets: ["Measure clamp thickness and rear clearance", "Check that an arm cannot strike the monitor", "Keep controls reachable from the seated position"] },
      { heading: "Evaluate useful controls", paragraphs: ["Dimming is often more useful than numerous color modes. Color-temperature adjustment can help match daylight and evening conditions, but published controls should be assessed alongside stability and light coverage."], bullets: ["Look for gradual brightness control", "Avoid exposed glare at eye level", "Route the power cable without crossing the work zone"] },
    ],
  },
  {
    slug: "ergonomic-accessories-home-office",
    title: "A Practical Guide to Home-Office Ergonomic Accessories",
    description: "Use accessories to support a sound workstation setup rather than expecting a single product to fix every discomfort.",
    category: "Ergonomics",
    intent: "Problem solving",
    readMinutes: 7,
    updated: "August 15, 2026",
    takeaways: ["Adjust the workstation before adding products", "Change one variable at a time", "Seek professional advice for persistent pain"],
    sections: [
      { heading: "Begin with the workstation", paragraphs: ["Accessories work best after basic chair height, screen position, input placement, and work habits are addressed. A product cannot compensate for a setup that forces prolonged reaching or an unsuitable viewing height."], bullets: ["Place frequently used inputs close to the body", "Adjust the screen for comfortable viewing", "Vary posture and take regular movement breaks"] },
      { heading: "Match the accessory to the problem", paragraphs: ["A footrest can support feet that do not reach the floor after chair adjustment. A monitor arm can improve screen positioning. An external keyboard can make a raised laptop practical. Each item should address an identified constraint."], bullets: ["Write down the specific problem before shopping", "Check compatibility and adjustment limits", "Avoid products that merely move the problem elsewhere"] },
      { heading: "Know the limit of buying advice", paragraphs: ["Comfort is individual, and persistent pain, numbness, or weakness deserves qualified medical or ergonomic assessment. Product guidance is not diagnosis or treatment."], bullets: ["Stop using an accessory that worsens symptoms", "Retain return options while evaluating fit", "Use measured changes rather than buying several items at once"] },
    ],
  },
  {
    slug: "desk-charging-station-setup",
    title: "Build a Cleaner Desk Charging Station",
    description: "Plan ports, power, device placement, and cable access before choosing a charging hub or station.",
    category: "Charging",
    intent: "Setup guide",
    readMinutes: 6,
    updated: "August 15, 2026",
    takeaways: ["Inventory devices and power needs", "Keep heat and cable strain under control", "Leave one flexible charging position"],
    sections: [
      { heading: "Inventory the devices", paragraphs: ["List the devices charged at the desk, how often they charge, their connector types, and whether their original power supplies are required. This prevents buying a hub with the wrong mix of ports."], bullets: ["Separate charging needs from high-speed data needs", "Record devices with unusually high power requirements", "Plan for one guest or future device without excessive unused capacity"] },
      { heading: "Choose a safe location", paragraphs: ["A charging station should be reachable without occupying the main work area. Keep ventilation around power electronics, avoid unsupported hanging adapters, and prevent connectors from bending sharply."], bullets: ["Do not bury warm adapters under papers or fabric", "Keep liquids away from power connections", "Mount only with hardware suitable for the surface"] },
      { heading: "Control cables without making them permanent", paragraphs: ["Use reusable ties, clips, or a routed tray so individual cables can be replaced. Label similar connectors and retain enough slack to connect a device without pulling the hub."], bullets: ["Keep one charging cable accessible", "Route data and power according to equipment instructions", "Recheck the setup when adding a new device"] },
    ],
  },
];

export function getGuide(slug: string) {
  return guides.find((guide) => guide.slug === slug);
}
