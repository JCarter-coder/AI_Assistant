import tkinter as tk

# A tooltip class to provide info over buttons when hovered
class ToolTip:
    def __init__(self, widget, text, delay=500):
        # the button that will be targeted
        self.widget = widget
        # text in the tooltip
        self.text = text
        # delay before visible
        self.delay = delay
        # hide the tooltip window
        self.tipwindow = None
        # ID given by .after(), so we can reference it to cancel later
        self.id = None
        # placeholder
        self.x = self.y = 0
        # when hovered over, schedule to appear
        widget.bind("<Enter>", self.enter)
        # when not hovered over, schedule to hide the tooltip
        widget.bind("<Leave>", self.leave)
        # when the button is clicke, schedule to hide the tooltip
        widget.bind("<ButtonPress>", self.leave)
    
    def enter(self, event=None):
        # start the timer to show the tooltip
        self.schedule()

    def leave(self, event=None):
        # cancel pending schedules
        self.unschedule()
        # destroy the tooltip
        self.hidetip()

    def schedule(self):
        # clear previous timers to avoid getting duplicates
        self.unschedule()
        # set id to schedule timer and display tooltip after delay
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        # cancel if a timer is already running
        if self.id:
            self.widget.after_cancel(self.id)
            # reset ID so no timer is pending
            self.id = None
        
    def showtip(self, event=None):
        # if tooltip is already visible or has not text, don't show
        if self.tipwindow or not self.text:
            return
        # return coordinates relative to the widget
        x, y, cx, cy = self.widget.bbox("insert") or (0,0,0,0)
        # convert to absolute screen coordinates
        # offset slightly above and to the right of widget
        x = x + self.widget.winfo_rootx() + 20
        y = y + cy + self.widget.winfo_rooty() - 30
        # create new top-level window, i.e. tooltip
        self.tipwindow = tw = tk.Toplevel(self.widget)
        # remove default window components
        tw.wm_overrideredirect(True)
        # place tooltip
        tw.wm_geometry(f"+{x}+{y}")
        # create label to display
        label = tk.Label(
            tw, text=self.text, justify="left",
            background="white", foreground="black", relief="solid", borderwidth=1,
            font=("tahoma", "16", "normal")
        )
        # display padded label
        label.pack(ipadx=4, ipady=2)

    def hidetip(self):
        # if tooltip exists, destroy it
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None