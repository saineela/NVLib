import customtkinter as ctk
from tkinter import filedialog
import json
from PIL import Image, ImageDraw, ImageTk
import base64
import io
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class BaseWrapper:
    def __init__(self, widget, layout_info):
        self.widget = widget
        self.layout_info = layout_info
        self.is_visible = True

    def toggle_visibility(self):
        if self.is_visible:
            self.widget.place_forget()
        else:
            self.widget.place(x=self.layout_info['x'], y=self.layout_info['y'])
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
            self.widget.configure(font=(current_font.cget("family"), current_font.cget("size"), new_weight))


class ButtonWrapper(BaseWrapper):
    def on_click(self, command):
        self.widget.configure(command=command)

class ValueWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, hint_text="", hint_color="grey"):
        super().__init__(widget, layout_info)
        self.hint_text = hint_text
        self.hint_color = hint_color

    def text(self, new_text=None):
        if new_text is None:
            if isinstance(self.widget, ctk.CTkEntry):
                return self.widget.get()
            elif isinstance(self.widget, ctk.CTkTextbox):
                value = self.widget.get("1.0", "end-1c")
                if value == self.hint_text and self.widget.cget("text_color")[1] == self.hint_color:
                    return ""
                return value
            return None
        else:
            if isinstance(self.widget, ctk.CTkEntry):
                self.widget.delete(0, "end")
                self.widget.insert(0, new_text)
            elif isinstance(self.widget, ctk.CTkTextbox):
                self.widget.delete("1.0", "end")
                self.widget.insert("1.0", new_text)
                self.widget.configure(text_color=self.widget.cget("text_color")[0])


class CheckWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, variable):
        super().__init__(widget, layout_info)
        self.variable = variable

    def is_checked(self):
        return self.variable.get()

    def on_toggle(self, command):
        self.widget.configure(command=command)

class ToggleWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, variable):
        super().__init__(widget, layout_info)
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
    def __init__(self, widget, layout_info, progress_bar, label):
        super().__init__(widget, layout_info)
        self.progress_bar = progress_bar
        self.label = label

    def set(self, value):
        normalized_value = value / 100.0
        self.progress_bar.set(normalized_value)
        if self.label:
            self.label.configure(text=f"{int(value)}%")

class SelectWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, variable):
        super().__init__(widget, layout_info)
        self.variable = variable

    def get(self):
        return self.variable.get()

    def on_select(self, command):
        self.widget.configure(command=command)

class RadioGroupWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, variable):
        super().__init__(widget, layout_info)
        self.variable = variable
    
    def get(self):
        return self.variable.get()

    def on_select(self, command):
        self.variable.trace_add("write", lambda name, index, mode: command(self.get()))

class SpinnerWrapper(BaseWrapper):
    def __init__(self, widget, layout_info, entry, min_val, max_val):
        super().__init__(widget, layout_info)
        self.entry = entry
        self.min_val = min_val
        self.max_val = max_val
    
    def get(self):
        try:
            return int(self.entry.get())
        except ValueError:
            return self.min_val

    def set(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(value))

class NVLibParser:
    def __init__(self, master):
        self.master = master
        self.widgets = {}
        self.image_references = []
        self.radio_groups = {}

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
        width = canvas_props.get('width', 800)
        height = canvas_props.get('height', 600)
        title = canvas_props.get('title', 'NVLib Generated GUI')
        self.master.geometry(f"{width}x{height}")
        self.master.title(title)
        self.master.resizable(False, False)

        components_data = layout.get('components', [])
        
        containers = {c['id']: c for c in components_data if c.get('type') in ['CardView', 'Panel', 'RadioGroup']}
        children = [c for c in components_data if c.get('type') not in ['CardView', 'Panel', 'RadioGroup']]

        for cid, data in containers.items():
            self.create_component(data, self.master)

        for data in children:
            parent = self.master
            parent_x, parent_y = 0, 0
            for cid, container_data in containers.items():
                cx, cy = container_data.get('x'), container_data.get('y')
                cw, ch = container_data.get('width'), container_data.get('height')
                dx, dy = data.get('x'), data.get('y')
                
                if (cx <= dx < cx + cw) and (cy <= dy < cy + ch):
                    parent = self.widgets[cid]['widget']
                    parent_x, parent_y = cx, cy
                    break 
            
            self.create_component(data, parent, parent_x, parent_y)
        
        return self.widgets

    def create_component(self, data, parent, parent_x=0, parent_y=0):
        comp_type = data.get('type')
        props = data.get('properties', {})
        comp_id = data.get('id')
        x, y, w, h = data.get('x'), data.get('y'), data.get('width'), data.get('height')
        
        rel_x, rel_y = x - parent_x, y - parent_y

        font_family = props.get('fontFamily', 'Arial')
        font_size = props.get('fontSize', 10)
        font_weight = "bold" if props.get('bold') else "normal"
        custom_font = ctk.CTkFont(family=font_family, size=font_size, weight=font_weight)

        widget = None
        variable = None
        wrapper_extras = {}

        if comp_type == 'Button':
            widget = ctk.CTkButton(parent, width=w, height=h, text=props.get('text'), 
                                     text_color=props.get('textColor'),
                                     fg_color=props.get('backgroundColor'),
                                     font=custom_font,
                                     corner_radius=props.get('cornerRadius', 8))
        
        elif comp_type == 'Label':
            text = props.get('iconName') or props.get('text')
            widget = ctk.CTkLabel(parent, width=w, height=h, text=text, text_color=props.get('textColor'), font=custom_font, fg_color="transparent")

        elif comp_type == 'TextBox':
            widget = ctk.CTkEntry(parent, width=w, height=h,
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
            widget = ctk.CTkTextbox(parent, width=w, height=h, text_color=props.get('textColor'), 
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
                img = img.resize((w, h), Image.Resampling.LANCZOS)
                radius = props.get('cornerRadius', 0)
                opacity = props.get('opacity', 1.0)
                processed_img = self._process_image(img, radius, opacity)

                ctk_image = ctk.CTkImage(light_image=processed_img, dark_image=processed_img, size=(w, h))
                widget = ctk.CTkLabel(parent, width=w, height=h, image=ctk_image, text="", fg_color="transparent")
                self.image_references.append(ctk_image)
            except Exception as e:
                widget = ctk.CTkLabel(parent, width=w, height=h, text="Image Error", fg_color="red")

        elif comp_type in ['CardView', 'Panel']:
            widget = ctk.CTkFrame(parent, width=w, height=h, fg_color=props.get('backgroundColor'),
                                   corner_radius=props.get('cornerRadius', 8))
        
        elif comp_type == 'Checkbox':
            variable = ctk.BooleanVar(value=props.get('checked', False))
            widget = ctk.CTkCheckBox(parent, width=w, height=h, text=props.get('text'), variable=variable, font=custom_font,
                                       text_color=props.get('textColor'), fg_color=props.get('checkedColor'))

        elif comp_type == 'ToggleButton':
            variable = ctk.IntVar(value=1 if props.get('checked') else 0)
            widget = ctk.CTkSwitch(parent, width=w, height=h, text=props.get('text', ''), variable=variable, font=custom_font,
                                     progress_color=props.get('onColor'), button_color=props.get('offColor'))

        elif comp_type == 'Slider':
            widget = ctk.CTkSlider(parent, width=w, height=h, from_=props.get('min',0), to=props.get('max',100),
                                   progress_color=props.get('progressColor'), button_color=props.get('buttonColor'))
            widget.set(props.get('value', 50))

        elif comp_type == 'ProgressBar':
            widget = ctk.CTkFrame(parent, width=w, height=h, fg_color="transparent")
            progress_bar = ctk.CTkProgressBar(widget, width=w, height=h, progress_color=props.get('progressColor'))
            progress_bar.set(props.get('value', 50) / 100.0)
            progress_bar.place(x=0, y=0)
            
            label = None
            if props.get('showPercentage'):
                label = ctk.CTkLabel(widget, text=f"{props.get('value', 50)}%", font=custom_font, text_color=props.get('textColor'), fg_color="transparent")
                pos = props.get('percentagePosition', 'center')
                relx = 0.5 if pos == 'center' else (0.05 if pos == 'left' else 0.95)
                anchor = 'center' if pos == 'center' else ('w' if pos == 'left' else 'e')
                label.place(relx=relx, rely=0.5, anchor=anchor)
            wrapper_extras = {'progress_bar': progress_bar, 'label': label}

        elif comp_type == 'Dropdown':
            variable = ctk.StringVar(value=props.get('text'))
            options = props.get('options', '').split('\n')
            if not options: options = [""]
            widget = ctk.CTkOptionMenu(parent, width=w, height=h, variable=variable, values=options, font=custom_font,
                                         text_color=props.get('textColor'), fg_color=props.get('backgroundColor'),
                                         dropdown_fg_color=props.get('backgroundColor'),
                                         dropdown_text_color=props.get('textColor'),
                                         dropdown_hover_color=props.get('selectionColor'))
        
        elif comp_type == 'RadioGroup':
            variable = ctk.StringVar(value=props.get('checkedValue'))
            widget = ctk.CTkFrame(parent, width=w, height=h, fg_color="transparent")
            
            group_label = ctk.CTkLabel(widget, text=props.get('label', ''), font=custom_font, text_color=props.get('textColor'))
            group_label.pack(anchor='w')

            options = props.get('options', '').split('\n')
            for opt in options:
                radio = ctk.CTkRadioButton(widget, text=opt, variable=variable, value=opt, font=custom_font,
                                           text_color=props.get('textColor'), fg_color=props.get('checkedColor'))
                radio.pack(anchor='w', pady=2)

        elif comp_type == 'Spinner':
            min_val, max_val = props.get('min', 0), props.get('max', 100)
            bg_color = props.get('backgroundColor', 'white')
            text_color = props.get('textColor', 'black')
            
            widget = ctk.CTkFrame(parent, width=w, height=h, fg_color=bg_color, corner_radius=props.get('cornerRadius', 8))
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

            minus_btn = ctk.CTkButton(widget, text="-", width=h-4, height=h-4, command=decrement, fg_color="transparent", text_color=text_color, hover=False, font=custom_font)
            plus_btn = ctk.CTkButton(widget, text="+", width=h-4, height=h-4, command=increment, fg_color="transparent", text_color=text_color, hover=False, font=custom_font)
            
            minus_btn.grid(row=0, column=0, padx=(2,0), pady=2)
            entry.grid(row=0, column=1, sticky="nsew")
            plus_btn.grid(row=0, column=2, padx=(0,2), pady=2)
            
            wrapper_extras = {'entry': entry, 'min_val': min_val, 'max_val': max_val}

        if widget:
            layout_info = {'x': rel_x, 'y': rel_y, 'width': w, 'height': h}
            widget.place(x=rel_x, y=rel_y)
            self.widgets[comp_id] = {'widget': widget, 'layout': layout_info, 'type': comp_type, 'variable': variable, **wrapper_extras}

class AutoGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.widgets = {}
        self._icon = None
        self.configure(fg_color="white")

    def __getattr__(self, name):
        if name in self.widgets:
            info = self.widgets[name]
            comp_type = info['type']
            
            if comp_type == 'Button':
                return ButtonWrapper(info['widget'], info['layout'])
            elif comp_type in ['TextBox', 'TextArea']:
                return ValueWrapper(info['widget'], info['layout'], **info.get('wrapper_info', {}))
            elif comp_type == 'Checkbox':
                return CheckWrapper(info['widget'], info['layout'], info['variable'])
            elif comp_type == 'RadioGroup':
                return RadioGroupWrapper(info['widget'], info['layout'], info['variable'])
            elif comp_type == 'ToggleButton':
                return ToggleWrapper(info['widget'], info['layout'], info['variable'])
            elif comp_type == 'Dropdown':
                return SelectWrapper(info['widget'], info['layout'], info['variable'])
            elif comp_type == 'Slider':
                return SliderWrapper(info['widget'], info['layout'])
            elif comp_type == 'ProgressBar':
                return ProgressWrapper(info['widget'], info['layout'], info['progress_bar'], info['label'])
            elif comp_type == 'Spinner':
                return SpinnerWrapper(info['widget'], info['layout'], info['entry'], info['min_val'], info['max_val'])
            else:
                return BaseWrapper(info['widget'], info['layout'])
        raise AttributeError(f"'AutoGUI' object has no attribute '{name}'")

    def build_gui(self, file_path):
        for widget in self.winfo_children():
            widget.destroy()
        
        resolved_layout_path = resource_path(file_path)

        parser = NVLibParser(self)
        self.widgets = parser.build_from_json(resolved_layout_path)
        if self.widgets is None:
            self.widgets = {}

    def set_title(self, title):
        self.title(title)

    def set_background(self, color):
        self.configure(fg_color=color)
        
    def set_icon(self, image_path):
        try:
            resolved_icon_path = resource_path(image_path)
            image = Image.open(resolved_icon_path)
            self._icon = ImageTk.PhotoImage(image)
            self.wm_iconphoto(False, self._icon)
        except Exception as e:
            print(f"Error setting icon: {e}. Make sure the path is correct and it's a valid image file.")

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
