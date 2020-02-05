#GRtag v.1 December 2019 by NMA
import os.path
import os
import mutagen
from mutagen.easyid3 import EasyID3
import tkinter as tk
from tkinter import filedialog, messagebox
import re

# https://pyinstaller.readthedocs.io/en/stable/runtime-information.html#run-time-information

import sys
if hasattr(sys, '_MEIPASS'):
    #print(os.listdir('_MEIPASS'))
    mydir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
else:
    mydir ="."




class Transliterate():
    
# class to transliterate any greek text following the ELOT743 conventions
# used as Transliterate.translit(txt)
    TT ={}
    @staticmethod
    def build_table():
        lookup = {}
        with open(os.path.join(mydir,'elot_743.txt'), 'r', encoding='utf-8') as elot:
            for line in elot:
                if '#' not in line:
                    letter = line.replace(',','').split('\t')
                    gr, en = letter[0].split(), letter[1].split()
                    # print(gr, en)
                    for _i in range(2):
                        # print(_i)
                        Transliterate.TT[gr[_i+1]] = en[_i]
                    if len(gr) == 4: Transliterate.TT[gr[3]] = en[-1]
        with open(os.path.join(mydir,'greek_utf.txt'), 'r', encoding='utf-8') as utf:
            for line in utf:
                if 'GREEK SMALL LETTER' in line :
                    letter = re.findall(r"GREEK SMALL LETTER ([A-Z]*) ", line, re.I)
                    lookup[letter[0].strip()] = lookup.get(letter[0].strip(), []) + [line[0]]

        # append the transliteration table with accented characters from lookup
        new_tt = []
        for t in Transliterate.TT:
            for let in lookup.values():
                if t in let and len(let)>1:
                    for l in let:
                        new_tt.append( (l, Transliterate.TT[t]))
        for (l,t) in new_tt:
            Transliterate.TT[l] = t
        # print table
        # for l in Transliterate.TT:
        #     print(l,Transliterate.TT[l])

    @staticmethod
    def translit(text):
        # drop non ascii characters
        #text = text.lower()
        out = ''
        for ch in text:
            if ch in Transliterate.TT:
                out += Transliterate.TT[ch]
            elif ord(ch) < 128:
                out += ch
        return out

class MyApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("MP3 Greek tag transliteration v.1.0")
        self.tk.call('wm', 'iconphoto', self._w, tk.PhotoImage(file=os.path.join(mydir,'logo.gif')))
        big_font = 'arial 18'
        self.logo = tk.PhotoImage(file= os.path.join(mydir,'logo.gif'))
        self.logo = self.logo.subsample(2,2)
        self.l = tk.Label(self, image=self.logo)
        self.l.grid(row=0, column=0)
        info_button = tk.Button(self, text='\nΟδηγίες\n', font=big_font, \
                                command=lambda:InfoWindow(self))
        info_button.grid(row=0, column=1, sticky='nsew')
        select_button = tk.Button(self, text='\nΕπιλογή μουσικής\n', font=big_font, command=self.set_file)
        select_button.grid(row=0, column=2, sticky='nsew')
        exit_button = tk.Button(self, text='\nΈξοδος\n', font=big_font, command=self.destroy)
        exit_button.grid(row=0, column=3, sticky='nsew')
        self.info = tk.Text(self, height= 30, width=75, bg='#eff0f1')
        self.info.tag_configure('t', font=('arial', 12))
        self.info.tag_configure('tb', font=('arial', 12, 'bold'))
        self.info.grid(row=1, columnspan=4)
        self.resizable(False, False)

    def set_file(self):
        dir_name = filedialog.askdirectory()
        if dir_name:
            count_mp3 = 0
            for r,d,f in os.walk(dir_name):
                count_mp3 += len([x for x in f if x.endswith('.mp3')])
            ans = messagebox.askyesno('', 'Θέλετε να γίνει επεξεργασία {} αρχείων mp3 που βρίσκονται στον φάκελο {}?'\
                                      .format(count_mp3, dir_name))
            if ans:
                self.transform(dir_name, modify=True)

    def stringify(self, l):
        return "["+",".join(l)+"]"

    def transform(self, dir, modify=False):
        count_errors = 0
        count_display = {}
        self.info.delete('1.0', 'end')
        for r, d, f in os.walk(dir):
            for file_name in f:
                out = ""
                if file_name.endswith('mp3'):
                    fname = os.path.join(r, file_name)
                    # title, artist, album, composer = '','', '',''
                    try:
                        # mutagen.id3.Encoding = "cp1253"
                        audio = EasyID3(fname)
                        out += '\nΑρχικές ετικέτες του τραγουδιού: '+fname +'\n'
                        if 'artist' in audio:
                            out+= 'ARTIST:' + self.stringify(audio['artist']) +'\n'
                        if 'composer' in audio:
                            out += 'COMPOSER:' + self.stringify(audio['composer']) +'\n'
                        if 'title' in audio:
                            out += 'TITLE:' + self.stringify(audio['title']) +'\n'
                        if 'album' in audio:
                            out += 'ALBUM:' + self.stringify(audio['album']) +'\n'
                        display = self.create_ascii_display(audio, file_name)
                        out += '\nΝέες ετικέτες:'
                        for d,v in display.items(): out += d+":"+self.stringify(v)+"\n"
                        if not display:
                            count = 3
                        else:
                            count = sum([1 for x in display if display[x]])
                        count_display[count] = count_display.get(count, 0) + 1
                        if modify and display:
                            for k in display:
                                if display[k]:
                                    audio[k] = display[k]
                                else:
                                    audio[k] = ""
                            audio.save()
                    except KeyError as e:
                        out += 'error with file' + str(e) + file_name +'\n'
                        count_errors += 1
                    except mutagen.id3._util.ID3NoHeaderError as e:
                        out += 'Header error', + str(e) + file_name +'\n'
                        count_errors += 1
                self.info.insert('end', out, 't')
        out = '\nΣφάλμα σε:'+ str(count_errors) + 'αρχεία\n' if count_errors else "\n"
        out += 'Μετατροπή ετικετών σε συνολικά {} αρχεία.\n'.format(sum(count_display.values()))
        self.info.insert('end', out, 'tb')
        self.info.see('end')
        self.info.config(state='disabled')

    def check_ascii(self, text):
        return all(ord(char) < 128 for char in text)

    def check_greek(self, text):
        return all([ord(char) < 128 or ord("ά") <= ord(char.lower()) <= ord("ώ") for char in text])

    def transliterate(self, text):
        if isinstance(text, list): text = text[0]
        if not self.check_ascii(text):
            text = text.lower()
            return ' '.join(x.capitalize() for x in Transliterate.translit(text).split())
        else: return text

    def create_ascii_display(self, audio, fname):
        display = {"artist": [], "title": [], "album": []}
        for d in display:
            if d in audio.keys():
                for din in audio[d]:
                    if self.check_greek(din):
                        display[d].append(self.transliterate(din))
                        break
        if not display['title']:
            if fname.split()[0].isdigit(): title = " ".join(fname.split()[1:])
            else: title = " ".join(fname.split())
            title = title.replace('.mp3', '')
            display['title'].append(self.transliterate(title))
        if not display['artist']:
            for k in audio:
                if 'artist' in k:
                    for x in audio[k]:
                        if self.check_greek(x):
                            display['artist'].append(self.transliterate(x))
                            break
        return display


class InfoWindow(tk.Toplevel):
    def __init__(self, root):
        tk.Toplevel.__init__(self, root)
        self.root = root
        # self.r = lambda: random.randint(0, 255) # τυχαίος αριθμός από 0..255
        self.create_window()

    def create_window(self):
        self.x = int(self.root.geometry().split('+')[-2]) + 50
        self.y = int(self.root.geometry().split('+')[-1]) + 50
        #self.window = tk.Toplevel()  # Το παράθυρο με τις πληροφορίες
        self.geometry('+{}+{}'.format(self.x, self.y))
        self.info = tk.Text(self, height= 30, width=80)
        self.info.tag_configure('t', font=('arial', 12))
        self.info.tag_configure('tb', font=('arial', 18, 'bold'))
        self.info.grid(column=0, row=0)
        info_text = '''GRtag v1.0\n'''
        self.info.insert('end', info_text, 'tb')
        info_text = '''To GRtag μετατρέπει τις ετικέτες αρχείων mp3 που είναι στα Ελληνικά
σε χαρακτήρες ascii, ώστε να τις εμφανίζουν συσκευές ήχου (πχ στο
αυτοκίνητο). Παράδειγμα: Χ.Αλεξίου γίνεται H.Alexiou.
- Επηρεάζει τις ετικέτες artist, title, album.
- Ακολουθεί το πρότυπο ΕΛΟΤ743 στη μετατροπή.

Οδηγίες χρήσης:
Επιλέξτε τον φάκελο που βρίσκονται τα μουσικά σας αρχεία (Επιλογή
μουσικής).
Θα γίνει μετατροπή σε όλα τα αρχεία mp3 του φακέλου που επιλέξατε
και όλων των υποφακέλων του.
\n'''
        self.info.insert('end', info_text, 't')
        self.img = tk.PhotoImage(file=os.path.join(mydir,'car.gif'))
        self.img = self.img.subsample(2, 2)
        self.info.image_create('end', image=self.img)
        self.info.insert('end', " >>> ", 'tb')
        self.img2 = tk.PhotoImage(file=os.path.join(mydir,'car2.gif'))
        self.img2 = self.img2.subsample(2, 2)
        self.info.image_create('end', image=self.img2)
        self.info.config(state='disabled')
        self.button = tk.Button(self, text = "\nok\n", bd = 4, font="arial 20", command = self.destroy)
        self.button.grid(row=1, column=0, sticky='nsew')
        self.resizable(False, False)

def main():
    Transliterate.build_table()
    window = MyApp()
    window.mainloop()


if __name__ == "__main__":
    main()

