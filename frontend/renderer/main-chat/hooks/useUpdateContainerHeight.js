import { useEffect } from "react"
import { ButtonsBarHeight } from "../../common/constants"

const useUpdateContainerHeight = (ref) => {
  useEffect(() => {
    const updateHistoryContainerHeight = () => {
      const headerHeight = ButtonsBarHeight
      const controlPanelHeight = ButtonsBarHeight
      const inputBox = document.querySelector(".input-box-wrapper")
      const inputBoxHeight = inputBox ? inputBox.offsetHeight : 0
      const availableHeight =
        window.innerHeight - 2 * headerHeight - inputBoxHeight
      // console.log(
      //   `HistoryContainerHeight: windowInnerHeight ${window.innerHeight} chatHistoryWrapperHeight ${availableHeight}`
      // )
      document.documentElement.style.setProperty(
        "--chat-history-wrapper-height",
        `${availableHeight}px`
      )
    }

    // Initial height calculation
    updateHistoryContainerHeight()
    // Create a ResizeObserver to watch for changes in the size of the input box
    const inputBox = document.querySelector(".message-input")
    if (inputBox) {
      const resizeObserver = new ResizeObserver(updateHistoryContainerHeight)
      resizeObserver.observe(inputBox)
    }
    // Add event listener for window resize
    window.addEventListener("resize", updateHistoryContainerHeight)

    // Cleanup on component unmount
    return () => {
      if (inputBox) {
        resizeObserver.disconnect()
      }
      window.removeEventListener("resize", updateHistoryContainerHeight)
    }
  }, [ref])
}

export default useUpdateContainerHeight
