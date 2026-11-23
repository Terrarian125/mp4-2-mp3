import os, sys, subprocess, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox

def resource_path(name):
    return os.path.join(sys._MEIPASS if getattr(sys,"frozen",False) else os.path.dirname(os.path.abspath(__file__)), name)
def no_console_kwargs():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name=="nt" else {}

class App:
    def __init__(self,root):
        self.root=root; root.title("MP4 to MP3"); root.geometry("650x460"); root.minsize(520,400)
        try: root.iconbitmap(resource_path("app.ico"))
        except Exception: pass
        self.files=[]; self.out=tk.StringVar(); self.rate=tk.StringVar(value="192"); self.status=tk.StringVar(value="MP4ファイルを追加してください。"); self.busy=False
        f=ttk.Frame(root,padding=12); f.pack(fill="both",expand=True)
        ttk.Label(f,text="MP4 → MP3 一括変換",font=("Meiryo UI",16,"bold")).pack(anchor="w",pady=(0,10))
        r=ttk.Frame(f); r.pack(fill="x"); ttk.Button(r,text="ファイル追加",command=self.add).pack(side="left"); ttk.Button(r,text="リストをクリア",command=self.clear).pack(side="left",padx=8)
        self.lb=tk.Listbox(f,height=12,selectmode="extended"); self.lb.pack(fill="both",expand=True,pady=8)
        r=ttk.Frame(f); r.pack(fill="x"); ttk.Label(r,text="出力先:").pack(side="left"); ttk.Entry(r,textvariable=self.out).pack(side="left",fill="x",expand=True,padx=6); ttk.Button(r,text="参照",command=self.folder).pack(side="left")
        r=ttk.Frame(f); r.pack(fill="x",pady=5); ttk.Label(r,text="ビットレート:").pack(side="left"); ttk.Combobox(r,textvariable=self.rate,values=["128","192","256","320"],state="readonly",width=8).pack(side="left",padx=6); ttk.Label(r,text="kbps").pack(side="left")
        self.pb=ttk.Progressbar(f,mode="determinate"); self.pb.pack(fill="x",pady=5); ttk.Label(f,textvariable=self.status).pack(anchor="w")
        self.btn=ttk.Button(f,text="変換開始",command=self.convert); self.btn.pack(anchor="e",pady=8); root.protocol("WM_DELETE_WINDOW",self.close)
    def add(self):
        for p in filedialog.askopenfilenames(title="MP4選択",filetypes=[("MP4","*.mp4"),("All files","*.*")]):
            if p not in self.files: self.files.append(p); self.lb.insert("end",p)
        if self.files and not self.out.get(): self.out.set(os.path.dirname(self.files[0]))
    def clear(self):
        if not self.busy: self.files=[]; self.lb.delete(0,"end"); self.pb["value"]=0
    def folder(self):
        d=filedialog.askdirectory()
        if d:self.out.set(d)
    def convert(self):
        if self.busy:return
        if not self.files: messagebox.showwarning("確認","MP4を追加してください。"); return
        if not self.out.get(): messagebox.showwarning("確認","出力先を選んでください。"); return
        exe=resource_path("ffmpeg.exe")
        if not os.path.isfile(exe): messagebox.showerror("エラー","ffmpeg.exeが見つかりません。"); return
        self.busy=True; self.btn.config(state="disabled"); threading.Thread(target=self.worker,args=(exe,self.out.get(),self.rate.get()),daemon=True).start()
    def worker(self,exe,out,rate):
        total=len(self.files); fails=[]
        os.makedirs(out,exist_ok=True)
        for i,p in enumerate(self.files,1):
            self.root.after(0,lambda i=i,p=p:self.status.set(f"変換中 ({i}/{total}): {os.path.basename(p)}"))
            target=os.path.join(out,os.path.splitext(os.path.basename(p))[0]+".mp3")
            try:
                res=subprocess.run([exe,"-y","-i",p,"-vn","-codec:a","libmp3lame","-b:a",rate+"k",target],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,**no_console_kwargs())
                if res.returncode: fails.append(p)
            except Exception: fails.append(p)
            self.root.after(0,lambda i=i:self.pb.configure(value=i/total*100))
        self.root.after(0,lambda:self.finish(total,fails))
    def finish(self,total,fails):
        self.busy=False; self.btn.config(state="normal")
        if fails: self.status.set(f"完了: {total-len(fails)}/{total}成功"); messagebox.showwarning("完了",f"{total-len(fails)}件成功、{len(fails)}件失敗しました。")
        else: self.status.set(f"完了: {total}/{total}件"); messagebox.showinfo("完了",f"{total}件の変換が完了しました。")
    def close(self):
        if self.busy: messagebox.showwarning("変換中","変換完了まで閉じられません。")
        else:self.root.destroy()
if __name__=="__main__":
    root=tk.Tk(); App(root); root.mainloop()
