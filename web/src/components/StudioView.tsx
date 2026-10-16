import type { ReactNode } from "react";
import { motion, useReducedMotion } from "motion/react";
import { motionIdentity } from "../motion";
export default function StudioView({ children }: { children: ReactNode }) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className="studio-view"
      initial={reduced ? false : { opacity: 0, y: 9 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: motionIdentity.standard,
        ease: motionIdentity.ease,
      }}
    >
      {children}
    </motion.div>
  );
}
