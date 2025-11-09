"""
Graphical User Interface for Nunalleq OCR.

A simple, user-friendly GUI for archaeologists with no programming experience.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
import queue
from typing import Optional
import sys

from .detector import ArtifactDetector
from .renamer import ArtifactRenamer


class NunalleqGUI:
    """Simple GUI for artifact photo processing."""

    def __init__(self, root):
        self.root = root
        self.root.title("Nunalleq Artifact Photo Organizer")
        self.root.geometry("800x700")

        # State
        self.input_folder = None
        self.output_folder = None
        self.processing = False
        self.message_queue = queue.Queue()

        # Setup UI
        self.setup_ui()

        # Start message processor
        self.process_messages()

    def setup_ui(self):
        """Create the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title
        title = ttk.Label(
            main_frame,
            text="Nunalleq Artifact Photo Organizer",
            font=('Arial', 16, 'bold')
        )
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Instructions
        instructions = ttk.Label(
            main_frame,
            text="This tool reads artifact numbers from photos and renames them automatically.\n"
                 "Your original photos will NOT be modified - renamed copies are saved to a new folder.",
            wraplength=700,
            justify=tk.LEFT
        )
        instructions.grid(row=1, column=0, columnspan=3, pady=(0, 20))

        # Step 1: Input folder
        step1_frame = ttk.LabelFrame(main_frame, text="Step 1: Select Photos to Process", padding="10")
        step1_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        step1_frame.columnconfigure(1, weight=1)

        ttk.Label(step1_frame, text="Folder with photos:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.input_label = ttk.Label(step1_frame, text="No folder selected", foreground="gray")
        self.input_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(step1_frame, text="Browse...", command=self.select_input).grid(row=0, column=2)

        ttk.Label(
            step1_frame,
            text="Tip: This can be a folder on an external hard drive. It will not be modified.",
            font=('Arial', 9),
            foreground="blue"
        ).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # Step 2: Output folder
        step2_frame = ttk.LabelFrame(main_frame, text="Step 2: Where to Save Renamed Photos", padding="10")
        step2_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        step2_frame.columnconfigure(1, weight=1)

        ttk.Label(step2_frame, text="Save renamed photos to:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.output_label = ttk.Label(step2_frame, text="No folder selected", foreground="gray")
        self.output_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(step2_frame, text="Browse...", command=self.select_output).grid(row=0, column=2)

        ttk.Label(
            step2_frame,
            text="Tip: Choose a folder on your computer (not the external drive).",
            font=('Arial', 9),
            foreground="blue"
        ).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # Options
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Include photos in subfolders",
            variable=self.recursive_var
        ).grid(row=0, column=0, sticky=tk.W)

        ttk.Label(
            options_frame,
            text="(e.g., if photos are organized in folders like 'Artwork', 'Bowls', etc.)",
            font=('Arial', 9),
            foreground="gray"
        ).grid(row=1, column=0, sticky=tk.W, padx=(25, 0))

        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))

        self.preview_btn = ttk.Button(
            button_frame,
            text="Preview (Check First)",
            command=self.preview,
            width=25
        )
        self.preview_btn.grid(row=0, column=0, padx=(0, 10))

        self.process_btn = ttk.Button(
            button_frame,
            text="Process Photos",
            command=self.process,
            width=25,
            style='Accent.TButton'
        )
        self.process_btn.grid(row=0, column=1)

        # Progress
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        self.progress_frame.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.grid(row=1, column=0)

        # Results
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        main_frame.rowconfigure(7, weight=1)

        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            height=15,
            width=70,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Configure tags for colored text
        self.results_text.tag_config("success", foreground="green")
        self.results_text.tag_config("error", foreground="red")
        self.results_text.tag_config("warning", foreground="orange")
        self.results_text.tag_config("info", foreground="blue")
        self.results_text.tag_config("bold", font=('Arial', 10, 'bold'))

    def select_input(self):
        """Select input folder."""
        folder = filedialog.askdirectory(title="Select Folder with Artifact Photos")
        if folder:
            self.input_folder = Path(folder)
            self.input_label.config(text=str(self.input_folder), foreground="black")
            self.log(f"Selected input folder: {self.input_folder}", "info")

    def select_output(self):
        """Select output folder."""
        folder = filedialog.askdirectory(title="Select Where to Save Renamed Photos")
        if folder:
            self.output_folder = Path(folder)
            self.output_label.config(text=str(self.output_folder), foreground="black")
            self.log(f"Selected output folder: {self.output_folder}", "info")

    def validate_inputs(self):
        """Check if inputs are valid."""
        if not self.input_folder:
            messagebox.showerror("Error", "Please select a folder with photos to process.")
            return False

        if not self.input_folder.exists():
            messagebox.showerror("Error", f"Input folder does not exist:\n{self.input_folder}")
            return False

        if not self.output_folder:
            messagebox.showerror("Error", "Please select where to save renamed photos.")
            return False

        return True

    def preview(self):
        """Preview what will happen without making changes."""
        if not self.validate_inputs():
            return

        if self.processing:
            messagebox.showwarning("Busy", "Already processing. Please wait.")
            return

        self.clear_results()
        self.log("Starting preview...\n", "bold")
        self.log("This is READ-ONLY - no files will be modified.\n", "info")

        # Run in background thread
        thread = threading.Thread(target=self._preview_worker, daemon=True)
        thread.start()

    def _preview_worker(self):
        """Worker thread for preview."""
        try:
            self.set_processing(True)

            detector = ArtifactDetector()
            renamer = ArtifactRenamer(detector=detector)

            self.queue_message("Scanning for photos...\n", "info")

            previews = renamer.preview_batch(
                self.input_folder,
                pattern="*.jpg",
                recursive=self.recursive_var.get()
            )

            if not previews:
                self.queue_message("No photos found matching the criteria.\n", "warning")
                self.queue_message("Make sure the folder contains .jpg files.\n", "info")
                return

            self.queue_message(f"Found {len(previews)} photos\n\n", "bold")

            success_count = sum(1 for p in previews if "✓" in p['status'])

            self.queue_message(f"Successfully detected: {success_count} photos\n", "success")
            self.queue_message(f"Failed to detect: {len(previews) - success_count} photos\n\n", "error")

            # Show some examples
            self.queue_message("Example results:\n", "bold")
            for preview in previews[:10]:
                if "✓" in preview['status']:
                    self.queue_message(f"  ✓ {preview['original']} → {preview['new_name']}\n", "success")
                else:
                    self.queue_message(f"  ✗ {preview['original']} - {preview['status']}\n", "error")

            if len(previews) > 10:
                self.queue_message(f"\n... and {len(previews) - 10} more photos\n", "info")

            self.queue_message(f"\nReady to process {success_count} photos.\n", "bold")
            self.queue_message("Click 'Process Photos' to create renamed copies.\n", "info")

        except Exception as e:
            self.queue_message(f"Error during preview: {e}\n", "error")
        finally:
            self.set_processing(False)

    def process(self):
        """Process and rename photos."""
        if not self.validate_inputs():
            return

        if self.processing:
            messagebox.showwarning("Busy", "Already processing. Please wait.")
            return

        # Confirm with user
        result = messagebox.askyesno(
            "Confirm",
            f"This will:\n\n"
            f"1. Read photos from:\n   {self.input_folder}\n\n"
            f"2. Create renamed copies in:\n   {self.output_folder}\n\n"
            f"Your original photos will NOT be modified.\n\n"
            f"Continue?"
        )

        if not result:
            return

        self.clear_results()
        self.log("Starting photo processing...\n", "bold")
        self.log("Your original photos will remain untouched.\n", "info")

        # Run in background thread
        thread = threading.Thread(target=self._process_worker, daemon=True)
        thread.start()

    def _process_worker(self):
        """Worker thread for processing."""
        try:
            self.set_processing(True)

            detector = ArtifactDetector()
            renamer = ArtifactRenamer(detector=detector, dry_run=False, backup=True)

            self.queue_message("Processing photos...\n", "info")

            results = renamer.rename_batch(
                self.input_folder,
                output_dir=self.output_folder,
                pattern="*.jpg",
                overwrite=False,
                recursive=self.recursive_var.get()
            )

            self.queue_message(f"\n{'='*50}\n", "")
            self.queue_message("PROCESSING COMPLETE\n", "bold")
            self.queue_message(f"{'='*50}\n\n", "")

            self.queue_message(f"Total photos processed: {results['total']}\n", "info")
            self.queue_message(f"Successfully renamed: {results['success']}\n", "success")
            self.queue_message(f"Failed: {results['failed']}\n", "error" if results['failed'] > 0 else "info")

            if results['log_file']:
                self.queue_message(f"\nDetailed log saved to:\n{results['log_file']}\n", "info")

            if results['success'] > 0:
                self.queue_message(f"\nRenamed photos saved to:\n{self.output_folder}\n", "success")

            if results['failed'] > 0:
                self.queue_message("\nSome photos could not be processed:\n", "warning")
                for item in results['results']:
                    if not item['success']:
                        self.queue_message(f"  ✗ {item['original']}\n", "error")

            # Show completion message
            if results['success'] > 0:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Complete",
                    f"Successfully processed {results['success']} photos!\n\n"
                    f"Renamed photos saved to:\n{self.output_folder}"
                ))

        except Exception as e:
            self.queue_message(f"\nERROR: {e}\n", "error")
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred:\n{e}"))
        finally:
            self.set_processing(False)

    def set_processing(self, processing: bool):
        """Update processing state."""
        self.processing = processing

        def update():
            if processing:
                self.preview_btn.config(state=tk.DISABLED)
                self.process_btn.config(state=tk.DISABLED)
                self.progress.start(10)
                self.progress_label.config(text="Processing...")
            else:
                self.preview_btn.config(state=tk.NORMAL)
                self.process_btn.config(state=tk.NORMAL)
                self.progress.stop()
                self.progress_label.config(text="")

        self.root.after(0, update)

    def log(self, message: str, tag: str = ""):
        """Add message to results text."""
        self.results_text.config(state=tk.NORMAL)
        if tag:
            self.results_text.insert(tk.END, message, tag)
        else:
            self.results_text.insert(tk.END, message)
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)

    def clear_results(self):
        """Clear results text."""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state=tk.DISABLED)

    def queue_message(self, message: str, tag: str = ""):
        """Queue a message to be displayed (thread-safe)."""
        self.message_queue.put((message, tag))

    def process_messages(self):
        """Process queued messages."""
        try:
            while True:
                message, tag = self.message_queue.get_nowait()
                self.log(message, tag)
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_messages)


def main():
    """Launch the GUI."""
    root = tk.Tk()

    # Set theme
    style = ttk.Style()
    style.theme_use('clam')

    # Create app
    app = NunalleqGUI(root)

    # Center window
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    # Run
    root.mainloop()


if __name__ == '__main__':
    main()
