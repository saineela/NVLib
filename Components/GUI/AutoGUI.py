import customtkinter as ctk
from tkinter import filedialog
import json
from PIL import Image, ImageDraw, ImageTk
import base64
import io
import os
import sys
import atexit
import tempfile

def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Component Wrapper Classes for the Simplified API ---

class BaseWrapper:
    def __init__(self, widget, layout_info, font_info):
        self.widget = widget
        self.layout_info = layout_info
        self.font_info = font_info
        self.is_visible = True

    def _rescale_font(self, scale_factor):
        if not self.font_info:
            return
        
        new_size = int(self.font_info['size'] * scale_factor)
        if new_size < 1: new_size = 1
        
        try:
            new_font = ctk.CTkFont(family=self.font_info['family'], 
                                   size=new_size, 
                                   weight=self.font_info['weight'])
            self.widget.configure(font=new_font)
        except Exception as e:
            # This can happen if the font isn't found, especially during rapid resizing.
            pass


    def toggle_visibility(self):
        if self.is_visible:
            self.widget.place_forget()
        else:
            self.widget.place(**self.layout_info)
        self.is_visible = not self.is_visible

    def text(self, new_text=None):
        if new_text is None:
            return self.widget.cget("text")
        else:
            self.widget.configure(text=new_text)

    def text_color(self, new_color=None):
        if new_color is None:
            return self.widget.cget("text_color")
        else:
            self.widget.configure(text_color=new_color)

    def background_color(self, new_color=None):
        if new_color is None:
            return self.widget.cget("fg_color")
        else:
            self.widget.configure(fg_color=new_color)
            
    def bold(self, is_bold=None):
        current_font = self.widget.cget("font")
        if is_bold is None:
            return current_font.cget("weight") == "bold"
        else:
            new_weight = "bold" if is_bold else "normal"
            self.font_info['weight'] = new_weight
            self.widget.configure(font=(current_font.cget("family"), current_font.cget("size"), new_weight))


class ButtonWrapper(BaseWrapper):
    def on_click(self, command):
        self.widget.configure(command=command)

class ValueWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, font_info, hint_text="", hint_color="grey"):
        super().__init__(widget, layout_info, font_info)
        self.hint_text = hint_text
        self.hint_color = hint_color

    def text(self, new_text=None):
        if new_text is None:
            # Getter
            if isinstance(self.widget, ctk.CTkEntry):
                return self.widget.get()
            elif isinstance(self.widget, ctk.CTkTextbox):
                value = self.widget.get("1.0", "end-1c")
                if value == self.hint_text and self.widget.cget("text_color")[1] == self.hint_color:
                    return ""
                return value
            return None
        else:
            # Setter
            if isinstance(self.widget, ctk.CTkEntry):
                self.widget.delete(0, "end")
                self.widget.insert(0, new_text)
            elif isinstance(self.widget, ctk.CTkTextbox):
                self.widget.delete("1.0", "end")
                self.widget.insert("1.0", new_text)
                # After setting text, ensure it's not using hint color
                self.widget.configure(text_color=self.widget.cget("text_color")[0])


class CheckWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, font_info, variable):
        super().__init__(widget, layout_info, font_info)
        self.variable = variable

    def is_checked(self):
        return self.variable.get()

    def on_toggle(self, command):
        self.widget.configure(command=command)

class ToggleWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, font_info, variable):
        super().__init__(widget, layout_info, font_info)
        self.variable = variable

    def is_on(self):
        return self.variable.get() == 1

    def on_toggle(self, command):
        self.widget.configure(command=command)

class SliderWrapper(BaseWrapper):
    def get(self):
        return self.widget.get()

    def set(self, value):
        self.widget.set(value)

class ProgressWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, font_info, progress_bar, label):
        super().__init__(widget, layout_info, font_info)
        self.progress_bar = progress_bar
        self.label = label

    def set(self, value):
        normalized_value = value / 100.0
        self.progress_bar.set(normalized_value)
        if self.label:
            self.label.configure(text=f"{int(value)}%")
    
    def _rescale_font(self, scale_factor):
        # Also scale the label inside the progress bar
        if self.label and self.font_info:
            new_size = int(self.font_info['size'] * scale_factor)
            if new_size < 1: new_size = 1
            try:
                new_font = ctk.CTkFont(family=self.font_info['family'], 
                                    size=new_size, 
                                    weight=self.font_info['weight'])
                self.label.configure(font=new_font)
            except: pass

class SelectWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, font_info, variable):
        super().__init__(widget, layout_info, font_info)
        self.variable = variable

    def get(self):
        return self.variable.get()

    def on_select(self, command):
        self.widget.configure(command=command)

class RadioGroupWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, font_info, variable, radios, label):
        super().__init__(widget, layout_info, font_info)
        self.variable = variable
        self.radios = radios
        self.label = label

    def get(self):
        return self.variable.get()

    def on_select(self, command):
        self.variable.trace_add("write", lambda name, index, mode: command(self.get()))
    
    def _rescale_font(self, scale_factor):
        # Scale the main label and all the radio button labels
        if not self.font_info: return
        new_size = int(self.font_info['size'] * scale_factor)
        if new_size < 1: new_size = 1
        try:
            new_font = ctk.CTkFont(family=self.font_info['family'], size=new_size, weight=self.font_info['weight'])
            if self.label:
                self.label.configure(font=new_font)
            for radio in self.radios:
                radio.configure(font=new_font)
        except: pass


class SpinnerWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, font_info, entry, min_val, max_val, buttons):
        super().__init__(widget, layout_info, font_info)
        self.entry = entry
        self.min_val = min_val
        self.max_val = max_val
        self.buttons = buttons
    
    def get(self):
        try:
            return int(self.entry.get())
        except ValueError:
            return self.min_val

    def set(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(value))
        
    def _rescale_font(self, scale_factor):
        # Override to do nothing, preventing spinner font from scaling
        pass

# --- Core GUI Building Logic ---

class NVLibParser:
    def __init__(self, master, debug=False):
        self.master = master
        self.widgets = {}
        self.image_references = []
        self.radio_groups = {}
        self.debug = debug
        self.original_canvas_width = 1
        self.original_canvas_height = 1

    def _process_image(self, img, radius, opacity):
        img = img.convert("RGBA")

        if opacity < 1.0:
            alpha = img.split()[3]
            alpha = alpha.point(lambda p: p * opacity)
            img.putalpha(alpha)

        if radius > 0:
            max_radius = min(img.size) // 2
            effective_radius = min(radius, max_radius)
            
            mask = Image.new('L', img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0) + img.size, radius=effective_radius, fill=255)
            img.putalpha(mask)
        
        return img

    def build_from_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                layout = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading layout file: {e}")
            return None

        canvas_props = layout.get('canvas', {})
        self.original_canvas_width = canvas_props.get('width', 800)
        self.original_canvas_height = canvas_props.get('height', 600)
        title = canvas_props.get('title', 'NVLib Generated GUI')
        self.master.geometry(f"{self.original_canvas_width}x{self.original_canvas_height}")
        self.master.title(title)
        self.master.resizable(True, True)
        self.master.minsize(self.original_canvas_width, self.original_canvas_height)

        components_data = layout.get('components', [])
        
        containers = {c['id']: c for c in components_data if c.get('type') in ['CardView', 'Panel']}
        all_other_components = [c for c in components_data if c.get('type') not in ['CardView', 'Panel']]

        for cid, data in containers.items():
            self.create_component(data, self.master, 0, 0, self.original_canvas_width, self.original_canvas_height)

        for data in all_other_components:
            parent = self.master
            parent_x, parent_y = 0, 0
            parent_w, parent_h = self.original_canvas_width, self.original_canvas_height
            
            for cid, container_data in containers.items():
                cx, cy = container_data.get('x'), container_data.get('y')
                cw, ch = container_data.get('width'), container_data.get('height')
                dx, dy = data.get('x'), data.get('y')
                
                if (cx <= dx < cx + cw) and (cy <= dy < cy + ch):
                    parent = self.widgets[cid]['widget']
                    parent_x, parent_y = cx, cy
                    parent_w, parent_h = cw, ch
                    break 
            
            self.create_component(data, parent, parent_x, parent_y, parent_w, parent_h)
        
        return self.widgets

    def create_component(self, data, parent, parent_x, parent_y, parent_w, parent_h):
        comp_type = data.get('type')
        props = data.get('properties', {})
        comp_id = data.get('id')
        x, y, w, h = data.get('x'), data.get('y'), data.get('width'), data.get('height')
        
        rel_x_offset, rel_y_offset = x - parent_x, y - parent_y

        relx = rel_x_offset / parent_w
        rely = rel_y_offset / parent_h
        relwidth = w / parent_w
        relheight = h / parent_h

        font_family = props.get('fontFamily', 'Arial')
        font_size = props.get('fontSize', 10)
        font_weight = "bold" if props.get('bold') else "normal"
        custom_font = ctk.CTkFont(family=font_family, size=font_size, weight=font_weight)
        font_info = {'family': font_family, 'size': font_size, 'weight': font_weight}

        widget = None
        variable = None
        wrapper_extras = {}
        layout_info = {}

        # Most widgets are created directly on the parent
        container = parent

        if comp_type == 'Button':
            widget = ctk.CTkButton(container, text=props.get('text'), 
                                   text_color=props.get('textColor'),
                                   fg_color=props.get('backgroundColor'),
                                   font=custom_font,
                                   corner_radius=props.get('cornerRadius', 8))
        
        elif comp_type == 'Label':
            text = props.get('iconName') or props.get('text')
            widget = ctk.CTkLabel(container, text=text, text_color=props.get('textColor'), font=custom_font, fg_color="transparent")

        elif comp_type == 'TextBox':
            widget = ctk.CTkEntry(container, 
                                  placeholder_text=props.get('hintText', ''),
                                  placeholder_text_color=props.get('hintColor', 'grey'),
                                  text_color=props.get('textColor'), 
                                  fg_color=props.get('backgroundColor'), 
                                  font=custom_font,
                                  border_width=0)
            
            initial_text = props.get('text', '')
            if initial_text:
                widget.insert(0, initial_text)

        elif comp_type == 'TextArea':
            widget = ctk.CTkTextbox(container, text_color=props.get('textColor'), 
                                    fg_color=props.get('backgroundColor'), font=custom_font,
                                    corner_radius=props.get('cornerRadius', 8))
            
            hint_text = props.get('hintText', '')
            hint_color = props.get('hintColor', 'grey')
            text_color = props.get('textColor', 'black')
            wrapper_extras = {'hint_text': hint_text, 'hint_color': hint_color}

            def on_focus_in(event):
                if widget.get("1.0", "end-1c") == hint_text:
                    widget.delete("1.0", "end")
                    widget.configure(text_color=text_color)

            def on_focus_out(event):
                if not widget.get("1.0", "end-1c"):
                    widget.insert("1.0", hint_text)
                    widget.configure(text_color=hint_color)

            initial_text = props.get('text', '')
            if initial_text:
                widget.insert('1.0', initial_text)
            else:
                widget.insert('1.0', hint_text)
                widget.configure(text_color=hint_color)

            widget.bind("<FocusIn>", on_focus_in)
            widget.bind("<FocusOut>", on_focus_out)

        elif comp_type == 'Image':
            base64_str = props.get('src', '').split(',')[-1]
            try:
                img_data = base64.b64decode(base64_str)
                img = Image.open(io.BytesIO(img_data)).convert("RGBA")
                
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(w,h))
                widget = ctk.CTkLabel(container, image=ctk_image, text="", fg_color="transparent")
                self.image_references.append(ctk_image)

            except Exception as e:
                widget = ctk.CTkLabel(container, text="Image Error", fg_color="red")


        elif comp_type in ['CardView', 'Panel']:
            widget = ctk.CTkFrame(container, fg_color=props.get('backgroundColor'),
                                  corner_radius=props.get('cornerRadius', 8))
        
        elif comp_type == 'Checkbox':
            variable = ctk.BooleanVar(value=props.get('checked', False))
            widget = ctk.CTkCheckBox(container, text=props.get('text'), variable=variable, font=custom_font,
                                     text_color=props.get('textColor'), fg_color=props.get('checkedColor'))

        elif comp_type == 'ToggleButton':
            variable = ctk.IntVar(value=1 if props.get('checked') else 0)
            widget = ctk.CTkSwitch(container, text=props.get('text', ''), variable=variable, font=custom_font,
                                   progress_color=props.get('onColor'), button_color=props.get('offColor'))

        elif comp_type == 'Slider':
            widget = ctk.CTkSlider(container, from_=props.get('min',0), to=props.get('max',100),
                                   progress_color=props.get('progressColor'), button_color=props.get('buttonColor'))
            widget.set(props.get('value', 50))

        elif comp_type == 'ProgressBar':
            widget = ctk.CTkFrame(container, fg_color="transparent")
            progress_bar = ctk.CTkProgressBar(widget, progress_color=props.get('progressColor'), fg_color=props.get('trackColor'))
            progress_bar.set(props.get('value', 50) / 100.0)
            progress_bar.pack(expand=True, fill='both')
            
            label = None
            wrapper_extras = {'progress_bar': progress_bar, 'label': label}


        elif comp_type == 'Dropdown':
            variable = ctk.StringVar(value=props.get('text'))
            options = props.get('options', '').split('\n')
            if not options: options = [""]
            size = [props.get('width', 120), props.get('height', 30)]
            bg_color = props.get('backgroundColor')
            text_color = props.get('textColor')
            hover_color = props.get('selectionColor')
            widget = ctk.CTkOptionMenu(container, variable=variable, values=options, font=custom_font,
                                       width=max(120, size[0]),
                                       height=max(30, size[1]),
                                       text_color=props.get('textColor'), fg_color=props.get('backgroundColor'),
                                       button_color=bg_color,
                                       button_hover_color=bg_color,
                                       dropdown_fg_color=bg_color,
                                       dropdown_text_color=text_color,
                                       dropdown_hover_color=hover_color,
                                       corner_radius=12)

        
        elif comp_type == 'RadioGroup':
            variable = ctk.StringVar(value=props.get('checkedValue'))
            widget = ctk.CTkFrame(container, fg_color="transparent")
            
            group_label = ctk.CTkLabel(widget, text=props.get('label', ''), font=custom_font, text_color=props.get('textColor'))
            group_label.pack(anchor='w')

            options = props.get('options', '').split('\n')
            radios = []
            for opt in options:
                radio = ctk.CTkRadioButton(widget, text=opt, variable=variable, value=opt, font=custom_font,
                                           text_color=props.get('textColor'), fg_color=props.get('checkedColor'))
                radio.pack(anchor='w', pady=2)
                radios.append(radio)
            wrapper_extras = {'radios': radios, 'label': group_label}

        elif comp_type == 'Spinner':
            min_val, max_val = props.get('min', 0), props.get('max', 100)
            bg_color = props.get('backgroundColor', 'white')
            text_color = props.get('textColor', 'black')
            
            widget = ctk.CTkFrame(container, width=w, height=h, fg_color=bg_color, corner_radius=8)
            widget.grid_propagate(False)
            widget.grid_columnconfigure(1, weight=1)
            widget.grid_rowconfigure(0, weight=1)

            entry = ctk.CTkEntry(widget, font=custom_font, text_color=text_color, border_width=0, fg_color="transparent", justify='center')
            entry.insert(0, str(props.get('value', 0)))
            
            def increment():
                try:
                    val = int(entry.get())
                    if val < max_val:
                        entry.delete(0, 'end')
                        entry.insert(0, str(val + 1))
                except ValueError: pass
            
            def decrement():
                try:
                    val = int(entry.get())
                    if val > min_val:
                        entry.delete(0, 'end')
                        entry.insert(0, str(val - 1))
                except ValueError: pass

            minus_btn = ctk.CTkButton(widget, text="-", command=decrement, fg_color="transparent", text_color=text_color, hover=False, font=custom_font, width=h-10)
            plus_btn = ctk.CTkButton(widget, text="+", command=increment, fg_color="transparent", text_color=text_color, hover=False, font=custom_font, width=h-10)
            
            minus_btn.grid(row=0, column=0, sticky='ns', padx=(5,2), pady=5)
            entry.grid(row=0, column=1, sticky='nsew')
            plus_btn.grid(row=0, column=2, sticky='ns', padx=(5,2), pady=5)
            
            wrapper_extras = {'entry': entry, 'min_val': min_val, 'max_val': max_val, 'buttons': [minus_btn, plus_btn]}

        if widget:
            if comp_type == 'Spinner':
                layout_info = {'relx': relx, 'rely': rely}
                widget.place(relx=relx, rely=rely)
            else:
                layout_info = {'relx': relx, 'rely': rely, 'relwidth': relwidth, 'relheight': relheight}
                widget.place(relx=relx, rely=rely, relwidth=relwidth, relheight=relheight)
            
            self.widgets[comp_id] = {'widget': widget, 'layout': layout_info, 'type': comp_type, 'font_info': font_info, 'variable': variable, **wrapper_extras}
            if self.debug:
                print(f"Created Component: '{comp_id}' of type '{comp_type}'")

class AutoGUI(ctk.CTk):
    def _resolve_path(self, path):
        try:
            base_path = sys._MEIPASS  # PyInstaller temp folder
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, path)

    def __init__(self):
        super().__init__()
        self.widgets = {}
        self._icon = None
        self.configure(fg_color="white")
        self.debug = False
        self.original_size = (1, 1) # width, height
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        if event.widget != self:
            return

        width_scale = self.winfo_width() / self.original_size[0]
        height_scale = self.winfo_height() / self.original_size[1]
        
        for name, info in self.widgets.items():
            try:
                if info['type'] != 'Spinner': # Exclude spinner from scaling
                    wrapper = self.__getattr__(name)
                    scale_factor = min(width_scale, height_scale)
                    wrapper._rescale_font(scale_factor)
            except (AttributeError, KeyError):
                pass


    def __getattr__(self, name):
        if name in self.widgets:
            info = self.widgets[name]
            comp_type = info['type']
            font_info = info.get('font_info') # Use .get for safety
            
            if comp_type == 'Button':
                return ButtonWrapper(info['widget'], info['layout'], font_info)
            elif comp_type in ['TextBox', 'TextArea']:
                return ValueWrapper(info['widget'], info['layout'], font_info, **info.get('wrapper_info', {}))
            elif comp_type == 'Checkbox':
                return CheckWrapper(info['widget'], info['layout'], font_info, info['variable'])
            elif comp_type == 'RadioGroup':
                return RadioGroupWrapper(info['widget'], info['layout'], font_info, info['variable'], info['radios'], info['label'])
            elif comp_type == 'ToggleButton':
                return ToggleWrapper(info['widget'], info['layout'], font_info, info['variable'])
            elif comp_type == 'Dropdown':
                return SelectWrapper(info['widget'], info['layout'], font_info, info['variable'])
            elif comp_type == 'Slider':
                return SliderWrapper(info['widget'], info['layout'], font_info)
            elif comp_type == 'ProgressBar':
                return ProgressWrapper(info['widget'], info['layout'], font_info, info['progress_bar'], info['label'])
            elif comp_type == 'Spinner':
                return SpinnerWrapper(info['widget'], info['layout'], font_info, info['entry'], info['min_val'], info['max_val'], info['buttons'])
            else: # For Panel, CardView, Image
                return BaseWrapper(info['widget'], info['layout'], font_info)
        raise AttributeError(f"'AutoGUI' object has no attribute '{name}'")

    def build_gui(self, file_path):
        for widget in self.winfo_children():
            widget.destroy()
        resolved_path = self._resolve_path(file_path)
        parser = NVLibParser(self, debug=self.debug)
        self.widgets = parser.build_from_json(resolved_path)
        if self.widgets is None:
            self.widgets = {}
        
        self.original_size = (parser.original_canvas_width, parser.original_canvas_height)

            
    def enable_debugging(self, enable=True):
        self.debug = enable

    def set_title(self, title):
        self.title(title)

    def set_background(self, color):
        self.configure(fg_color=color)
        
    def load_icon_font(self, path):
        try:
            ctk.FontManager.load_font(path)
        except Exception as e:
            print(f"Error loading icon font: {e}")

    def set_icon(self, image_path):
        resolved_path = self._resolve_path(image_path)
        try:
            img = Image.open(resolved_path)
            img = img.resize((32, 32), Image.Resampling.LANCZOS)
            temp_dir = tempfile.gettempdir()
            ico_path = os.path.join(temp_dir, f"autogui_icon_{os.getpid()}.ico")
            img.save(ico_path, format='ICO', sizes=[(32,32)])
            self.iconbitmap(ico_path)
            atexit.register(lambda: os.path.exists(ico_path) and os.remove(ico_path))
        except Exception as e:
            print(f"Failed to set icon: {e}")

    def load_new_gui(self):
        file_path = filedialog.askopenfilename(
            title="Select New GUI Layout File",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if file_path:
            self.build_gui(file_path)

    def close_gui(self):
        self.destroy()

    def run(self):
        self.mainloop()
