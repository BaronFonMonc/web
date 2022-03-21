const msgerForm = get(".msger-inputarea");
const msgerInput = get(".msger-input");
const msgerChat = get(".msger-chat");


//const socket = io.connect('http://127.0.0.1:5000');
const socket = io();


const username = document.getElementById("name_of_person").innerHTML;
//const username = current_user.id;

/*
socket.on('connect', () => {
    socket.send({'username': 'Service message', 'msg': 'User ' + username + ' has connected!', 'room': window.location.href});
});*/


const BOT_MSGS = [
  "Umm...?",
  "Same...",
  "Yeah",
  "Ummmm...",
  "Continue",
  "I'm listening",
  "Yeah I understand you. Keep going.",
  "So what next?",
  "Sometimes it's like I am talking to a wall",
  "Is it?",
  "No way!",
  "Wow!",
  "Sorry could you repeat that?",
  "Wow! We having so much fun here"
];

// Icons made by Freepik from www.flaticon.com
const BOT_IMG = "https://i.pinimg.com/originals/1e/95/5d/1e955db131fe1df6719a9445b94096d2.png";
const PERSON_IMG = "https://image.flaticon.com/icons/svg/145/145867.svg";
const BOT_NAME = "BOT";
const PERSON_NAME = username;

msgerForm.addEventListener("submit", event => {
  event.preventDefault();

  const msgText = msgerInput.value;
  if (!msgText) return;

  //appendMessage(PERSON_NAME, PERSON_IMG, "right", msgText);
  //msgerInput.value = "";

  //botResponse();
});

                $('#send_msg').on('click', () => {
                    const msgText = msgerInput.value;
                    if (!msgText) return;
                    socket.send({
                            'msg': msgerInput.value,
                            'username': username,
                            'room': window.location.href
                        });
                    $('#message_input').val('');
                    //appendMessage(PERSON_NAME, PERSON_IMG, "right", msgText);
                    msgerInput.value = "";
                    //botResponse();
                });


                socket.on('message', data => {
                    if (data.msg.length > 0) {
                        if (data.username === 'Service message') {
                            appendMessage(BOT_NAME, BOT_IMG, "left", data.msg);
                        } else {
                            if (PERSON_NAME==data.username) {
                                if ("msgs" in data) {
                                    appendMessageFull(data.msgs, "right");
                                }
                                else{
                                    appendMessage(PERSON_NAME, PERSON_IMG, "right", data.msg);
                                }
                            }
                            else{
                                if ("msgs" in data) {
                                    appendMessageFull(data.msgs, "left");
                                }
                                else{
                                    appendMessage(data.username, PERSON_IMG, "left", data.msg);
                                }
                            }
                        }
                        console.log('Received message');
                    }
                });


function appendMessageFull(ms, side) {
                if (PERSON_NAME.split(' ')[1] == 'RU'){
                temp = ms[2]['RU'].replace('?', '&quest');
                temp = temp.replace(' ', '%20');

                ms[5]='https://translator1.loca.lt/synthesize/'+temp+'?src_lang=ru';
               }
            else{
                temp = ms[2]['EN'].replace('?', '&quest');
                temp = temp.replace(' ', '%20');

                ms[5]='https://translator1.loca.lt/synthesize/'+temp+'?src_lang=en';
            }

    const msgHTML = `
    <div class="msg ${side}-msg">
      <div
        class="msg-img"
        style="background-image: url(https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png)"
      ></div>

      <div class="msg-bubble">
        <div class="msg-info">
            <div class="msg-info-name">${ms[1]} ${ms[4]}</div>
            <div class="msg-info-time">${ms[3]}</div>
        </div>
            <div class="msg-text">
                ${ms[2][PERSON_NAME.split(' ')[1]]}
            </div>
        </div>
      </div>

      <div class="msg ${side}-msg">
        <div
            class="msg-img"
            style="background-image: url(data:image/png;base64,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)"
        ></div>

        <div class="msg-bubble">
            <div class="msg-text">
                <audio src=${ms[5]} controls>Audio tag not supported</audio>
            </div>
        </div>
      </div>
    `;

  msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  msgerChat.scrollTop += 500;
}


function appendMessage(name, img, side, text) {
  //   Simple solution for small apps
  const msgHTML = `
    <div class="msg ${side}-msg">
      <div class="msg-img" style="background-image: url(${img})"></div>

      <div class="msg-bubble">
        <div class="msg-info">
          <div class="msg-info-name">${name}</div>
          <div class="msg-info-time">${formatDate(new Date())}</div>
        </div>

        <div class="msg-text">${text}</div>
      </div>
    </div>
  `;

  msgerChat.insertAdjacentHTML("beforeend", msgHTML);
  msgerChat.scrollTop += 500;
}

function botResponse() {
  const r = random(0, BOT_MSGS.length - 1);
  const msgText = BOT_MSGS[r];
  const delay = msgText.split(" ").length * 100;

  setTimeout(() => {
    appendMessage(BOT_NAME, BOT_IMG, "left", msgText);
  }, delay);
}

// Utils
function get(selector, root = document) {
  return root.querySelector(selector);
}

function formatDate(date) {
  const h = "0" + date.getHours();
  const m = "0" + date.getMinutes();

  return `${h.slice(-2)}:${m.slice(-2)}`;
}

function random(min, max) {
  return Math.floor(Math.random() * (max - min) + min);
}
