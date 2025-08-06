import cv2 as cv 
from dearpygui import dearpygui as dpg
import threading
import numpy as np
 
from detection import *
from db import *

class CameraStreamingApp:
    def __init__(self):
        self.streaming=False
        self.authenticated=False
        self.camera_frames={}
        self.camera_textures={}
        self.streaming_threads={}
        self.stop_flag={}
        self.cameras={}
        self.caps={}
        self.subcontainer_count=0
        auth_table()
        ip_table()
        self.setup_gui()
        
    def center_windows(self):
        viewport_width = dpg.get_viewport_width()
        viewport_height = dpg.get_viewport_height()
        
        login_x = (viewport_width - 350) // 2
        login_y = (viewport_height - 310) // 2
        dpg.set_item_pos("login_window", [login_x, login_y])
    
        reg_x = (viewport_width - 400) // 2
        reg_y = (viewport_height - 395) // 2
        dpg.set_item_pos("registration_window", [reg_x, reg_y])
    
        cam_x = (viewport_width - 350) // 2
        cam_y = (viewport_height - 350) // 2
        dpg.set_item_pos("add_cam_window", [cam_x, cam_y])

    def move_to_username_field(self, sender, app_data, user_data):
        dpg.focus_item("password")

    def submit_login(self, sender, app_data, user_data):
        self.login_callback()

    def move_to_reg_email(self, sender, app_data, user_data):
        dpg.focus_item("reg_email")

    def move_to_reg_password(self, sender, app_data, user_data):
        dpg.focus_item("reg_password")

    def move_to_reg_confirm_password(self, sender, app_data, user_data):
        dpg.focus_item("reg_conf_password")

    def submit_registration(self, sender, app_data, user_data):
        self.register_callback()

    def move_to_cam_password(self, sender, app_data, user_data):
        dpg.focus_item("cam_pass")

    def move_to_cam_ip(self, sender, app_data, user_data):
        dpg.focus_item("cam_ip")
        
    def submit_add_camera(self, sender, app_data, user_data):
        self.add_cam_callback()

    def make_full_screen(self,win_tag:str):
        dpg.set_primary_window(win_tag,True)

    def goto_login_window(self):
        dpg.show_item("login_window")
        dpg.hide_item("registration_window")
        dpg.set_value("registration_status","")
        dpg.set_value("reg_username","")
        dpg.set_value("reg_password","")
        dpg.set_value("reg_conf_password","")

    def login_callback(self):
        username=dpg.get_value("username")
        password=dpg.get_value("password")
        if authenticate_user(username,password):
            self.authenticated=True
            dpg.hide_item("login_window")
            dpg.show_item("main_window")
            self.make_full_screen("main_window")
            dpg.set_value("username","")
            dpg.set_value("password","")
            dpg.set_value("login_status","")
            self.refresh_cams()
        else:
            dpg.set_value("login_status","Invalid Credentials!!!")

    def add_cam_callback(self):
        username = dpg.get_value("cam_user")
        password = dpg.get_value("cam_pass")
        ip = dpg.get_value("cam_ip")
        if add_ip(username,password,ip):
            self.refresh_cams()
            self.start_cameras()
            dpg.hide_item("add_cam_window")
            dpg.set_value("add_cam_status","")
        else:
            dpg.set_value("cam_user","")
            dpg.set_value("cam_pass","")
            dpg.set_value("cam_ip","")
            dpg.set_value("add_cam_status","Please specify that all the fields are correct!!!")

        dpg.set_value("cam_user","")
        dpg.set_value("cam_pass","")
        dpg.set_value("cam_ip","")

    def goto_add_cam(self):
        dpg.show_item("add_cam_window")

    def goto_register_window(self):
        dpg.hide_item("login_window")
        dpg.show_item("registration_window")
        dpg.set_value("username","")
        dpg.set_value("password","")
        dpg.set_value("login_status","")

    def register_callback(self):
        username=dpg.get_value("reg_username")
        email=dpg.get_value("reg_email")
        password=dpg.get_value("reg_password")
        conf_password=dpg.get_value("reg_conf_password")
        if not username or not password or not email:
            dpg.set_value("registration_status","Username, Password and Email are required!!!")
            dpg.set_value("reg_username","")
            dpg.set_value("reg_email","")
            dpg.set_value("reg_password","")
            dpg.set_value("reg_conf_password","")
        elif check_username(username):
            dpg.set_value("registration_status","Username already taken")
            dpg.set_value("reg_username","")
            dpg.set_value("reg_password","")
            dpg.set_value("reg_conf_password","")
        elif(password!=conf_password):
            dpg.set_value("registration_status","Passwords don't match!!!")
            dpg.set_value("reg_password","")
            dpg.set_value("reg_conf_password","")
        else:
            dpg.set_value("registration_status","")
            dpg.set_value("reg_username","")
            dpg.set_value("reg_password","")
            dpg.set_value("reg_conf_password","")
            dpg.hide_item("registration_window")
            dpg.show_item("login_window")
            register_user(username,email,password)
    
    def remove_cam_callback(self,temp1,temp2,id):
        ip=self.cameras[id][2]
        f = remove_cam(ip)
        if f:
            self.stop_camera1(id)
            self.caps[id].release()
            del self.caps[id]
            self.refresh_cams()
            self.start_cameras()
        else:
            pass
    def create_cam_container(self,container_id):
        with dpg.group(tag=f"subcamera_container_{container_id}",parent="camera_container",horizontal=True):
            pass

    def create_display(self,id,ip,container_id):
        group_tag = f"group_{id}"
        texture_tag = f"texture_{id}"
        image_tag = f"image_{id}"

        with dpg.group(tag=group_tag,parent=f"subcamera_container_{container_id}"):
            dpg.add_text(f"camera-{id}:{ip}")
            dpg.add_button(label="Remove Camera",callback=self.remove_cam_callback,user_data=id)

            black_image = np.zeros((240, 320, 3), dtype=np.uint8)
            black_image_flat = black_image.ravel() / 255.0

            with dpg.texture_registry():
                dpg.add_raw_texture(320, 240, black_image_flat, tag=texture_tag, format=dpg.mvFormat_Float_rgb)
            
            dpg.add_image(texture_tag, tag=image_tag, width=320, height=240)

        self.camera_textures[id] = texture_tag
        
    def setup_gui(self):
        dpg.create_context()

        with dpg.font_registry():
            default_font = dpg.add_font("calibri-regular.ttf", 18)
            dpg.bind_font(default_font)
        
        with dpg.theme() as modern_theme:
            with dpg.theme_component(dpg.mvAll):
            # Colour palette
                 dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (248, 249, 250, 255))
                 dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (255, 255, 255, 255))
                 dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (241, 243, 244, 255))
                 dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (233, 236, 239, 255))
                 dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (255, 255, 255, 255))
            
            # Button styling
                 dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 123, 255, 255))
                 dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 86, 179, 255))
                 dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (0, 69, 134, 255))
            
            # Text colors
                 dpg.add_theme_color(dpg.mvThemeCol_Text, (33, 37, 41, 255))
                 dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (0, 123, 255, 76))

            # Frame styling
                 dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                 dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
                 dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6)
                 dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 12, 8)
                 dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 20)
                 dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 12)
    
        dpg.bind_theme(modern_theme)

        #Input Text Theme
        with dpg.theme() as input_text_theme:
             with dpg.theme_component(dpg.mvInputText):
                 dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (211, 211, 211, 255))            # Normal
                 dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (220, 235, 255, 255))     # Hover
                 dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (200, 220, 255, 255))      # Focused
                 dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 122, 204, 255))               # Border
                 dpg.add_theme_color(dpg.mvThemeCol_Text, (30, 30, 30, 255))                  # Text
                 dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                 dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
                 
        #Add Camera Window
        with dpg.window(label="",tag="add_cam_window",width=350,height=350,no_resize=True,no_move=True,no_collapse=True):
            with dpg.group(horizontal=True):
                 dpg.add_spacer(width=100)
                 dpg.add_text("Camera Registry", color=(0, 0, 0))
            dpg.add_separator()
            with dpg.group():
                dpg.add_input_text(label="username",tag="cam_user",width=200,on_enter=True,callback=self.move_to_cam_password)
                dpg.bind_item_theme("cam_user", input_text_theme)
                dpg.add_input_text(label="password",tag="cam_pass",width=200,on_enter=True,callback=self.move_to_cam_ip)
                dpg.bind_item_theme("cam_pass", input_text_theme)
                dpg.add_input_text(label="ip",tag="cam_ip",width=200,on_enter=True,callback=self.submit_add_camera)
                dpg.bind_item_theme("cam_ip", input_text_theme)
            dpg.add_separator()
            dpg.add_text("", tag="add_cam_status", color=(255, 0, 0))
            with dpg.group(horizontal=True):
                dpg.add_button(label="Add Camera",callback=self.add_cam_callback)

        #Login window 
        with dpg.window(label="",tag="login_window",width=350,height=310,no_resize=True,no_move=True,no_collapse=True,no_title_bar=True):
           
            with dpg.group(horizontal=True):
                 dpg.add_spacer(width=100)
                 dpg.add_text("Login Window", tag="login_heading")
            dpg.add_separator()

            with dpg.group():
                 dpg.add_input_text(label="username",tag="username",width=200,on_enter=True,callback=self.move_to_username_field)
                 dpg.bind_item_theme("username", input_text_theme)
                 dpg.add_input_text(label="password",tag="password",password=True,width=200,on_enter=True,callback=self.submit_login)
                 dpg.bind_item_theme("password", input_text_theme)
            
                
            dpg.add_separator()
            dpg.add_text("", tag="login_status", color=(255, 0, 0))
            with dpg.group(horizontal=True):
                dpg.add_button(label="Login",tag="login_btn",callback=self.login_callback)
                dpg.add_button(label="Register",tag="gotoregister_btn",callback=self.goto_register_window)
        
        #Registration window
        with dpg.window(label="",tag="registration_window",width=400,height=395,no_resize=True,no_collapse=True,no_move=True,no_title_bar=True):
           
            with dpg.group(horizontal=True):
                 dpg.add_spacer(width=100)
                 dpg.add_text("Registration Window", tag="registration_heading")
            dpg.add_separator()

            with dpg.group():
                dpg.add_input_text(label="username",tag="reg_username",width=200,on_enter=True,callback=self.move_to_reg_email)
                dpg.bind_item_theme("reg_username", input_text_theme)
                dpg.add_input_text(label="email",width=200,tag="reg_email",on_enter=True,callback=self.move_to_reg_password)
                dpg.bind_item_theme("reg_email", input_text_theme)
                dpg.add_input_text(label="password",width=200,tag="reg_password",password=True,on_enter=True,callback=self.move_to_reg_confirm_password)
                dpg.bind_item_theme("reg_password", input_text_theme)
                dpg.add_input_text(label="confirm password",width=200,tag="reg_conf_password",password=True,on_enter=True,callback=self.submit_registration)
                dpg.bind_item_theme("reg_conf_password", input_text_theme)
            
            dpg.add_separator()
            dpg.add_text("",tag="registration_status",color=(255,0,0))

            with dpg.group(horizontal=True):
                dpg.add_button(label="Register",tag="reg_btn",callback=self.register_callback)
                dpg.add_button(label="Back to Login",tag="gotologin_btn",callback=self.goto_login_window)

        #Main window
        with dpg.window(label="main window", tag="main_window",no_title_bar=True):
            
            with dpg.group(horizontal=True):
                dpg.add_button(label="Start All Cameras", callback=self.start_cameras)
                dpg.add_button(label="Stop All Cameras", callback=self.stop_cameras)
                dpg.add_button(label="Load All Cameras", callback=self.refresh_cams)
                dpg.add_button(label="Add Camera",callback=self.goto_add_cam)
            
            dpg.add_separator()
            
            with dpg.group(label="Running Status",tag="running_status"):
                dpg.add_text("Status: Everything is OK",tag="main_status1",color=(0,255,0),indent=1290)
                dpg.add_text("Status: Something went wrong",tag="main_status2",color=(255,0,0),indent=1290)
                dpg.add_separator()

            with dpg.child_window(label="Camera Feeds", tag="camera_container", height=-1,):
                with dpg.group(label="subcamera container",tag="subcamera_container_0",horizontal=True):
                    pass
        
        dpg.create_viewport(title="Collision Avoidance")
        dpg.set_viewport_clear_color((55, 71, 79))
        dpg.setup_dearpygui()
        dpg.hide_item("registration_window")
        dpg.hide_item("main_window")
        dpg.hide_item("add_cam_window")
        #maximizing my viewport it is completely unnecessary
        dpg.maximize_viewport()
        self.center_windows()
        self.make_full_screen("main_window")
        dpg.show_viewport()

        def on_viewport_resize():
           self.center_windows()
        dpg.set_viewport_resize_callback(on_viewport_resize)


    def start_streaming(self,id):
        username,password,ip = self.cameras[id][0],self.cameras[id][1],self.cameras[id][2]
        if not self.authenticated:
            return
        url=f"rtsp://{username}:{password}@{ip}/Streaming/Channels/102"
        cap=cv.VideoCapture(0)
        cap.set(cv.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            print(f"Error with oppening camera with {ip}")
        else:
            self.caps[id]=cap
            c_frames=0
            while True:
                isTrue,frame = cap.read()
                if isTrue:
                    frame = cv.resize(frame, (320, 240))
                    #if not c_frames%5==0:
                    #frame = detectNtrack(frame)
                    frame = avoid_collision(frame)
                    self.camera_frames[id] = frame
                    c_frames+=1
                else:
                    break
            cap.release()
            print(f"camera {id} with ip-{ip} stopprd streaming!!!")
    
    def start_camera1(self,id):
        if id not in self.streaming_threads or not self.streaming_threads[id].is_alive():
            thread = threading.Thread(
                target= self.start_streaming,
                args = (id,),
                daemon = True
            )
            thread.start()
            self.streaming_threads[id]=thread

    def start_cameras(self):
        for id in self.cameras.keys():
            self.start_camera1(id)
        self.streaming=True

    def stop_camera1(self,id):
        self.stop_flag[id]=True
        if id in self.camera_frames:
            frame = self.camera_frames[id]
            del self.camera_frames[id]

    def stop_cameras(self):
        for id in self.stop_flag.keys():
            self.stop_camera1(id)
        self.streaming=False

    def update_display(self):
        for id,frame in self.camera_frames.items():
            if id in self.camera_textures:
                texture_tag = self.camera_textures[id]

                frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                frame_normalized = frame_rgb.astype(np.float32) / 255.0
                frame_flat = frame_normalized.ravel()

                dpg.set_value(texture_tag, frame_flat)

    def refresh_cams(self):
        if not self.authenticated:
            return
        self.stop_cameras()
        for id in self.cameras.keys():
            dpg.delete_item(f"group_{id}")
            dpg.delete_item(f"image_{id}")
            dpg.delete_item(f"texture_{id}")
        for i in range(1,self.subcontainer_count+1):
            dpg.delete_item(f"subcamera_container_{i}")
        self.subcontainer_count=0
        self.camera_frames={}
        self.camera_textures={}
        self.cameras={}
        c,temp=0,0
        k,cameras1 = get_cameras()
        if(k==-1):
            dpg.set_value("main_status2","Status:Some error occured in fetching Camera IP")
            dpg.set_value("main_status1","")
        elif k==0:
            dpg.set_value("main_status1","Status:No camera detail is available")
            dpg.set_value("main_status2","")
        else:
            dpg.set_value("main_status1","Status:Everthing is ok")
            dpg.set_value("main_status2","")
            self.cameras=dict(enumerate(cameras1))
            for id,(username,password,ip) in self.cameras.items():
                temp+=1
                self.create_display(id,ip,self.subcontainer_count)
                if(temp%3==0): 
                    self.subcontainer_count+=1
                    self.create_cam_container(self.subcontainer_count)

    def run(self):
        while dpg.is_dearpygui_running():
            if self.authenticated and self.streaming:
                self.update_display()
            dpg.render_dearpygui_frame()
        
        self.stop_cameras()
        dpg.destroy_context()

if __name__ == "__main__":
    #dele()
    app = CameraStreamingApp()
    app.run()