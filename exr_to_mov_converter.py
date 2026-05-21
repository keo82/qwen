#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXR Sequence to MOV Converter
Converts EXR sequences to MOV with various codecs and colorspaces
Supports ACES color management workflow
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import subprocess
import threading
from pathlib import Path


class EXRtoMOVConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("EXR to MOV Converter")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Variables
        self.input_file_path = tk.StringVar()
        self.output_base_path = tk.StringVar()
        self.fps_value = tk.StringVar(value="24")
        
        # New variables for enhanced options
        self.input_colorspace_var = tk.StringVar(value="aces_ap0")
        self.output_colorspace_var = tk.StringVar(value="rec709")
        self.output_format_var = tk.StringVar(value="prores")
        self.anamorphic_var = tk.BooleanVar(value=False)
        
        self.log_text = None
        self.progress_var = tk.DoubleVar()
        self.is_converting = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Title
        title_label = ttk.Label(main_frame, text="EXR Sequence to MOV Converter", 
                                font=('Helvetica', 16, 'bold'))
        title_label.grid(row=row, column=0, columnspan=3, pady=(0, 20), sticky=tk.W)
        row += 1
        
        # Input file selection
        ttk.Label(main_frame, text="Input File (list of sequences):").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(1, weight=1)
        
        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_file_path, width=50)
        self.input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        
        ttk.Button(input_frame, text="Browse...", command=self.browse_input_file).grid(
            row=0, column=2, sticky=tk.W)
        row += 1
        
        # Help text for input file format
        help_text = ("Format: Each line should contain the path to an EXR sequence.\n"
                    "Use printf-style pattern like: /path/shot_0001.exr or /path/shot.%04d.exr\n"
                    "The program will auto-detect the sequence range.")
        ttk.Label(main_frame, text=help_text, foreground="gray", 
                 font=('Helvetica', 9)).grid(row=row, column=0, columnspan=3, 
                                            sticky=tk.W, pady=5)
        row += 1
        
        # Output base path
        ttk.Label(main_frame, text="Output Base Path:").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        row += 1
        
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        output_frame.columnconfigure(1, weight=1)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_base_path, width=50)
        self.output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        
        ttk.Button(output_frame, text="Browse...", command=self.browse_output_path).grid(
            row=0, column=2, sticky=tk.W)
        row += 1
        
        # FPS setting
        fps_frame = ttk.Frame(main_frame)
        fps_frame.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=5)
        ttk.Label(fps_frame, text="FPS:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.fps_entry = ttk.Entry(fps_frame, textvariable=self.fps_value, width=10)
        self.fps_entry.grid(row=0, column=1, sticky=tk.W)
        row += 1
        
        # Anamorphic correction checkbox
        anamorphic_frame = ttk.Frame(main_frame)
        anamorphic_frame.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=5)
        self.anamorphic_check = ttk.Checkbutton(anamorphic_frame, 
            text="Anamorphic Correction (unsqueeze 2x)", 
            variable=self.anamorphic_var)
        self.anamorphic_check.grid(row=0, column=0, sticky=tk.W)
        ttk.Label(anamorphic_frame, text="Corrects anamorphic lens squeeze (2x desqueeze)", 
                 foreground="gray", font=('Helvetica', 8)).grid(row=0, column=1, padx=(10, 0))
        row += 1
        
        # Colorspace settings section
        colorspace_section_label = ttk.Label(main_frame, text="Colorspace Settings:", 
                                             font=('Helvetica', 11, 'bold'))
        colorspace_section_label.grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
        row += 1
        
        # Input colorspace (EXR source)
        ttk.Label(main_frame, text="Input Colorspace (EXR):").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        
        input_cs_frame = ttk.Frame(main_frame)
        input_cs_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        input_colorspace_options = [
            ("ACES-2065-1 (AP0)", "aces_ap0"),
            ("ACES-AP1", "aces_ap1"),
            ("Linear (sRGB/Rec709)", "linear"),
            ("sRGB", "srgb"),
            ("Rec.709", "rec709"),
            ("Rec.2020", "rec2020"),
            ("P3-D65", "p3d65"),
        ]
        
        for i, (text, value) in enumerate(input_colorspace_options):
            ttk.Radiobutton(input_cs_frame, text=text, variable=self.input_colorspace_var, 
                          value=value).grid(row=i // 4, column=i % 4, padx=5, sticky=tk.W)
        row += 1
        
        # Output colorspace for MOV
        ttk.Label(main_frame, text="Output Colorspace (MOV):").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        
        output_cs_frame = ttk.Frame(main_frame)
        output_cs_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        output_colorspace_options = [
            ("Rec.709", "rec709"),
            ("sRGB", "srgb"),
            ("Rec.2020", "rec2020"),
            ("P3-D65", "p3d65"),
            ("ACES-AP1", "aces_ap1"),
        ]
        
        for i, (text, value) in enumerate(output_colorspace_options):
            ttk.Radiobutton(output_cs_frame, text=text, variable=self.output_colorspace_var, 
                          value=value).grid(row=0, column=i, padx=10, sticky=tk.W)
        row += 1
        
        # Output format selection
        ttk.Label(main_frame, text="Output Format:").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        
        format_frame = ttk.Frame(main_frame)
        format_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        format_options = [
            ("ProRes 422 HQ", "prores_hq"),
            ("ProRes 422", "prores"),
            ("ProRes 422 LT", "prores_lt"),
            ("H.264", "h264"),
        ]
        
        for i, (text, value) in enumerate(format_options):
            ttk.Radiobutton(format_frame, text=text, variable=self.output_format_var, 
                          value=value).grid(row=0, column=i, padx=10, sticky=tk.W)
        row += 1
        
        # Progress bar
        ttk.Label(main_frame, text="Progress:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), 
                              padx=(10, 0), pady=5)
        row += 1
        
        # Log area
        ttk.Label(main_frame, text="Log:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        row += 1
        
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=15, width=80, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        main_frame.rowconfigure(row, weight=1)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        self.convert_button = ttk.Button(button_frame, text="Start Conversion", 
                                        command=self.start_conversion)
        self.convert_button.grid(row=0, column=0, padx=10)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_conversion,
                                     state='disabled')
        self.stop_button.grid(row=0, column=1, padx=10)
        
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).grid(
            row=0, column=2, padx=10)
        
        # Add tooltips/information
        info_text = (
            "Instructions:\n"
            "1. Create a text file with paths to your EXR sequences (one per line)\n"
            "2. Select the text file using 'Browse...'\n"
            "3. Choose output base directory\n"
            "4. Set FPS and colorspace\n"
            "5. Click 'Start Conversion'\n\n"
            "Output structure: <shot_name>/comp/mov/<shot_name>_exr.mov"
        )
        info_label = ttk.Label(main_frame, text=info_text, foreground="blue",
                              font=('Helvetica', 9), justify=tk.LEFT)
        info_label.grid(row=row+1, column=0, columnspan=3, sticky=tk.W, pady=10)
    
    def browse_input_file(self):
        """Open file dialog to select input text file"""
        filename = filedialog.askopenfilename(
            title="Select input file list",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_file_path.set(filename)
    
    def browse_output_path(self):
        """Open directory dialog to select output base path"""
        directory = filedialog.askdirectory(title="Select output base directory")
        if directory:
            self.output_base_path.set(directory)
    
    def log(self, message):
        """Add message to log"""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def parse_sequence(self, sequence_path):
        """
        Parse an EXR sequence path to find all frames.
        Supports patterns like:
        - /path/shot_0001.exr (will find shot_*.exr)
        - /path/shot.%04d.exr
        - /path/shot.####.exr
        """
        sequence_path = sequence_path.strip()
        
        if not os.path.exists(sequence_path):
            # Try to detect pattern
            match = re.search(r'([%#\d]+d)', sequence_path)
            if match:
                # Pattern like %04d or ####
                pattern = sequence_path[:match.start()] + '*' + sequence_path[match.end():]
                base_dir = os.path.dirname(pattern)
                prefix = os.path.basename(pattern)
                
                # Find matching files
                if os.path.exists(base_dir):
                    files = sorted([f for f in os.listdir(base_dir) if f.startswith(prefix.split('*')[0])])
                    if files:
                        return [os.path.join(base_dir, f) for f in files]
            
            # Try to find directory and detect sequence
            parts = sequence_path.rsplit('.', 1)
            if len(parts) == 2:
                base = parts[0]
                ext = parts[1]
                dir_path = os.path.dirname(base)
                prefix = os.path.basename(base)
                
                # Remove trailing numbers from prefix
                prefix_clean = re.sub(r'[\d_]+$', '', prefix)
                
                if os.path.exists(dir_path):
                    files = sorted([f for f in os.listdir(dir_path) 
                                   if f.startswith(prefix_clean) and f.endswith(ext)])
                    if files:
                        return [os.path.join(dir_path, f) for f in files]
            
            return None
        
        # If it's a single file, find similar files in the directory
        if os.path.isfile(sequence_path):
            dir_path = os.path.dirname(sequence_path)
            base_name = os.path.basename(sequence_path)
            
            # Extract pattern
            match = re.match(r'(.+?)(\d+)(\.exr)$', base_name, re.IGNORECASE)
            if match:
                prefix = match.group(1)
                suffix = match.group(3)
                
                files = []
                for f in sorted(os.listdir(dir_path)):
                    if f.startswith(prefix) and f.endswith(suffix):
                        files.append(os.path.join(dir_path, f))
                
                return files if files else [sequence_path]
        
        return [sequence_path]
    
    def get_shot_name(self, sequence_files):
        """Extract shot name from sequence files"""
        if not sequence_files:
            return "unknown_shot"
        
        first_file = sequence_files[0]
        base_name = os.path.basename(first_file)
        
        # Remove frame number and extension
        shot_name = re.sub(r'[\d_]+\.exr$', '', base_name, flags=re.IGNORECASE)
        shot_name = shot_name.rstrip('_').rstrip('.')
        
        if not shot_name:
            shot_name = os.path.basename(os.path.dirname(first_file))
        
        return shot_name
    
    def convert_sequence(self, sequence_files, output_path, fps, input_colorspace, output_colorspace, 
                         output_format, anamorphic):
        """Convert a sequence of EXR files to MOV"""
        if not sequence_files:
            raise ValueError("No sequence files found")
        
        # Get image dimensions from first frame
        first_frame = sequence_files[0]
        
        # Use ffprobe to get dimensions
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            first_frame
        ]
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            dims = result.stdout.strip().split(',')
            src_width = int(dims[0])
            src_height = int(dims[1])
        except Exception as e:
            self.log(f"Warning: Could not probe dimensions, using default: {e}")
            src_width = 1920
            src_height = 1080
        
        # Calculate output dimensions (maintain aspect ratio, fit to 1920x1080)
        target_width = 1920
        target_height = 1080
        
        # Apply anamorphic desqueeze if enabled (2x unsqueeze - stretch width)
        if anamorphic:
            src_width = src_width * 2
            self.log(f"Anamorphic correction applied: {src_width/2}x{src_height} -> {src_width}x{src_height}")
        
        # Scale to fit within 1920 width while maintaining aspect ratio
        # Don't crop left/right - scale based on width
        scale_factor = target_width / src_width
        scaled_width = target_width  # Always scale to 1920 width
        scaled_height = int(src_height * scale_factor)
        
        # If scaled height is greater than 1080, we need to scale down more
        if scaled_height > target_height:
            scale_factor = target_height / src_height
            scaled_width = int(src_width * scale_factor)
            scaled_height = target_height
        
        # Calculate padding for letterboxing (top and bottom only)
        pad_left = 0  # No horizontal padding
        pad_top = (target_height - scaled_height) // 2
        
        # Build ffmpeg filter chain with input->output colorspace conversion
        colorspace_filter = self.get_colorspace_filter(input_colorspace, output_colorspace)
        
        filter_complex = (
            f"{colorspace_filter}, "
            f"scale={scaled_width}:{scaled_height}:flags=lanczos, "
            f"pad={target_width}:{target_height}:{pad_left}:{pad_top}:black"
        )
        
        # Detect sequence pattern from files
        dir_path = os.path.dirname(sequence_files[0])
        base_name = os.path.basename(sequence_files[0])
        
        # Extract pattern
        match = re.match(r'(.+?)(\d+)(\.exr)$', base_name, re.IGNORECASE)
        if match:
            prefix = match.group(1)
            num_digits = len(match.group(2))
            suffix = match.group(3)
            pattern = os.path.join(dir_path, f"{prefix}%0{num_digits}d{suffix}")
        else:
            # Fallback: use first file directly
            pattern = sequence_files[0]
        
        try:
            # Build codec and format settings based on output format selection
            codec_settings = self.get_codec_settings(output_format, output_colorspace)
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-framerate', str(fps),
                '-i', pattern,
                '-vf', filter_complex,
            ] + codec_settings + [output_path]
            
            self.log(f"Running: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Read output
            for line in process.stderr:
                if self.is_converting:
                    self.log(line.strip())
                else:
                    break
            
            process.wait()
            
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg failed with code {process.returncode}")
            
        except Exception as e:
            raise RuntimeError(f"FFmpeg error: {str(e)}")
    
    def get_colorspace_filter(self, input_colorspace, output_colorspace):
        """Get the appropriate colorspace conversion filter from input to output colorspace"""
        # Define gamma values for different colorspaces (simplified approach without OCIO)
        # For proper ACES workflow, OCIO configuration would be needed
        
        # Input gamma values (from linear/source)
        input_gammas = {
            'aces_ap0': 1.0,      # ACES-2065-1 is linear
            'aces_ap1': 1.0,      # ACES-AP1 is linear
            'linear': 1.0,        # Linear
            'srgb': 2.2,          # sRGB approx
            'rec709': 2.4,        # Rec.709 with 2.4 gamma
            'rec2020': 2.4,       # Rec.2020 with 2.4 gamma
            'p3d65': 2.6,         # P3-D65
        }
        
        # Output gamma values (to target)
        output_gammas = {
            'rec709': 0.4545,     # ~1/2.2 for Rec.709
            'srgb': 0.4545,       # ~1/2.2 for sRGB
            'rec2020': 0.4545,    # ~1/2.2 for Rec.2020
            'p3d65': 0.4545,      # ~1/2.2 for P3-D65
            'aces_ap1': 1.0,      # Keep linear for AP1
        }
        
        in_gamma = input_gammas.get(input_colorspace, 1.0)
        out_gamma = output_gammas.get(output_colorspace, 0.4545)
        
        # Calculate combined gamma correction
        # If input is linear (gamma=1), we just apply output gamma
        # If input has a gamma, we need to first linearize then apply output gamma
        if in_gamma == 1.0:
            # Source is linear, just apply output transfer function
            combined_gamma = out_gamma
        else:
            # Need to convert: source gamma -> linear -> output gamma
            combined_gamma = out_gamma * in_gamma
        
        return f'eq=gamma={combined_gamma:.4f}'

    def get_codec_settings(self, output_format, output_colorspace):
        """Get codec and format settings based on output format selection"""
        
        # Determine pixel format based on output colorspace
        if output_colorspace in ['rec709', 'rec2020', 'p3d65', 'aces_ap1']:
            pix_fmt = 'yuv422p10'  # 10-bit 4:2:2 for video colorspaces
        else:
            pix_fmt = 'yuv422p10'  # Default to 10-bit
        
        if output_format == 'prores_hq':
            return [
                '-c:v', 'prores_ks',
                '-profile:v', '4',  # ProRes 422 HQ
                '-pix_fmt', pix_fmt,
                '-colorspace', self.get_ffmpeg_colorspace(output_colorspace),
                '-color_primaries', self.get_ffmpeg_primaries(output_colorspace),
                '-color_trc', self.get_ffmpeg_trc(output_colorspace),
            ]
        elif output_format == 'prores':
            return [
                '-c:v', 'prores_ks',
                '-profile:v', '3',  # ProRes 422
                '-pix_fmt', pix_fmt,
                '-colorspace', self.get_ffmpeg_colorspace(output_colorspace),
                '-color_primaries', self.get_ffmpeg_primaries(output_colorspace),
                '-color_trc', self.get_ffmpeg_trc(output_colorspace),
            ]
        elif output_format == 'prores_lt':
            return [
                '-c:v', 'prores_ks',
                '-profile:v', '2',  # ProRes 422 LT
                '-pix_fmt', pix_fmt,
                '-colorspace', self.get_ffmpeg_colorspace(output_colorspace),
                '-color_primaries', self.get_ffmpeg_primaries(output_colorspace),
                '-color_trc', self.get_ffmpeg_trc(output_colorspace),
            ]
        elif output_format == 'h264':
            return [
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '18',  # High quality
                '-pix_fmt', 'yuv420p',  # H.264 typically uses 4:2:0
                '-colorspace', self.get_ffmpeg_colorspace(output_colorspace),
                '-color_primaries', self.get_ffmpeg_primaries(output_colorspace),
                '-color_trc', self.get_ffmpeg_trc(output_colorspace),
            ]
        else:
            # Default to ProRes 422
            return [
                '-c:v', 'prores_ks',
                '-profile:v', '3',
                '-pix_fmt', pix_fmt,
                '-colorspace', self.get_ffmpeg_colorspace(output_colorspace),
                '-color_primaries', self.get_ffmpeg_primaries(output_colorspace),
                '-color_trc', self.get_ffmpeg_trc(output_colorspace),
            ]
    
    def get_ffmpeg_colorspace(self, colorspace):
        """Get FFmpeg colorspace value"""
        mapping = {
            'rec709': 'bt709',
            'rec2020': 'bt2020nc',
            'p3d65': 'bt709',  # Closest match
            'aces_ap1': 'bt709',
            'srgb': 'bt709',
        }
        return mapping.get(colorspace, 'bt709')
    
    def get_ffmpeg_primaries(self, colorspace):
        """Get FFmpeg color primaries value"""
        mapping = {
            'rec709': 'bt709',
            'rec2020': 'bt2020',
            'p3d65': 'smpte432',
            'aces_ap1': 'bt709',
            'srgb': 'bt709',
        }
        return mapping.get(colorspace, 'bt709')
    
    def get_ffmpeg_trc(self, colorspace):
        """Get FFmpeg transfer characteristics value"""
        mapping = {
            'rec709': 'bt709',
            'rec2020': 'bt2020_10',
            'p3d65': 'bt709',
            'aces_ap1': 'linear',
            'srgb': 'iec61966_2_1',
        }
        return mapping.get(colorspace, 'bt709')
    
    def start_conversion(self):
        """Start the conversion process"""
        # Validate inputs
        if not self.input_file_path.get():
            messagebox.showerror("Error", "Please select an input file list")
            return
        
        if not os.path.exists(self.input_file_path.get()):
            messagebox.showerror("Error", "Input file does not exist")
            return
        
        if not self.output_base_path.get():
            messagebox.showerror("Error", "Please select an output base path")
            return
        
        if not os.path.exists(self.output_base_path.get()):
            messagebox.showerror("Error", "Output base path does not exist")
            return
        
        try:
            fps = float(self.fps_value.get())
            if fps <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Invalid FPS value")
            return
        
        # Start conversion in separate thread
        self.is_converting = True
        self.convert_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        
        thread = threading.Thread(target=self.run_conversion, daemon=True)
        thread.start()
    
    def run_conversion(self):
        """Run the conversion process (in background thread)"""
        try:
            # Read input file list
            with open(self.input_file_path.get(), 'r') as f:
                sequences = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            total_sequences = len(sequences)
            self.log(f"Found {total_sequences} sequence(s) to process")
            
            for i, sequence_path in enumerate(sequences):
                if not self.is_converting:
                    self.log("Conversion stopped by user")
                    break
                
                self.log(f"\nProcessing sequence {i+1}/{total_sequences}: {sequence_path}")
                self.update_progress((i / total_sequences) * 100)
                
                # Parse sequence
                sequence_files = self.parse_sequence(sequence_path)
                
                if not sequence_files:
                    self.log(f"Warning: Could not find files for sequence: {sequence_path}")
                    continue
                
                self.log(f"Found {len(sequence_files)} frames")
                
                # Get shot name
                shot_name = self.get_shot_name(sequence_files)
                self.log(f"Shot name: {shot_name}")
                
                # Create output directory structure: <shot_name>/comp/mov/
                output_dir = os.path.join(self.output_base_path.get(), shot_name, "comp", "mov")
                os.makedirs(output_dir, exist_ok=True)
                
                # Output filename: <shot_name>_exr.mov
                output_filename = f"{shot_name}_exr.mov"
                output_path = os.path.join(output_dir, output_filename)
                
                self.log(f"Output path: {output_path}")
                
                # Convert sequence with all new parameters
                input_colorspace = self.input_colorspace_var.get()
                output_colorspace = self.output_colorspace_var.get()
                output_format = self.output_format_var.get()
                anamorphic = self.anamorphic_var.get()
                fps = float(self.fps_value.get())
                
                self.convert_sequence(sequence_files, output_path, fps, 
                                     input_colorspace, output_colorspace, 
                                     output_format, anamorphic)
                
                self.log(f"Completed: {output_path}")
            
            if self.is_converting:
                self.log("\n=== Conversion completed successfully ===")
                self.update_progress(100)
                messagebox.showinfo("Success", "All sequences converted successfully!")
        
        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
        
        finally:
            self.is_converting = False
            self.root.after(0, lambda: self.convert_button.configure(state='normal'))
            self.root.after(0, lambda: self.stop_button.configure(state='disabled'))
    
    def stop_conversion(self):
        """Stop the conversion process"""
        self.is_converting = False
        self.log("Stopping conversion...")


def main():
    root = tk.Tk()
    app = EXRtoMOVConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
