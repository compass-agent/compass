import { useEffect } from "react";

const useScrollToBottom = (ref, dependency) => {
  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [dependency]);
};

export default useScrollToBottom;