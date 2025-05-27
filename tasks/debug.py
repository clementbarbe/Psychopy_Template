from psychopy import visual, event, core

# On désactive le test de framerate
win = visual.Window(fullscr=False, color='black', checkTiming=False)
text = visual.TextStim(win, color='white', height=0.1)

response = ''
while True:
    keys = event.getKeys()
    for key in keys:
        if key == 'escape':
            win.close()
            core.quit()
        elif key in ['return', 'num_enter']:
            print("Réponse :", response)
            win.close()
            core.quit()
        elif key == 'backspace':
            response = response[:-1]
        elif key in ['0','1','2','3','4','5','6','7','8','9']:
            response += key

        text.text = response
        text.draw()
        win.flip()
