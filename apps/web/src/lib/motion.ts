/** Shared, subtle motion presets. Kept small and fast (150-220ms). */

import type { Transition, Variants } from "motion/react"

export const easeOut: Transition = { duration: 0.2, ease: [0.22, 1, 0.36, 1] }

/** Page enter/exit used on route changes. */
export const pageMotion = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
  transition: easeOut,
}

/** Container that staggers its children in. */
export const listContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04 } },
}

/** Item used inside a staggered list/grid. */
export const listItem: Variants = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: easeOut },
}
