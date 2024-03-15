<script>
    import { onMount, onDestroy } from 'svelte';
    let users = []
    let errorMessage = '';
    let ws;
    $: newGuest = ''
    let userName = '';
    let userClicks = 0;
    const unique_id = localStorage.getItem('dXVpZA==')
    let storeData = localStorage.getItem('c3RvcmU=')

    function connect() {
        const hostname = window.location.hostname;
        const serverAddress = hostname === '121.173.41.66'
            ? 'ws://121.173.41.66:4001/ws'
            : 'ws://127.0.0.1:4001/ws';

        ws = new WebSocket(serverAddress);

        ws.onopen = () => {
            console.log('Connected');
            errorMessage = '';


            ws.send(JSON.stringify({"type": "uuid", "uuid": unique_id}))
            ws.send(JSON.stringify({"type": "address", "address": hostname}))

            if (storeData) {
                if (storeData === "False"){
                    newGuest = true
                } else {
                    newGuest = false
                }
            } else {
                localStorage.setItem('c3RvcmU=', "False")
                newGuest = true
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error', error);
            errorMessage = 'WebSocket 연결에 실패했습니다.';
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "users") {
                    users = data.users.map(user => ({ uuid: user.uuid, name: user.nickName, clicks: user.click }));
                    console.log(users)
                    function compare(a, b) {
                        return b.clicks - a.clicks
                    }
                    users = users.sort(compare)

                    let currentUser = users.find(user => user.uuid === unique_id);
                    if (currentUser) {
                        userName = currentUser.name;
                        userClicks = currentUser.clicks;
                    } else {
                        console.log('ERROR: No Stored data');
                    }
                } else if (data.type === "welcome") {
                    if (!unique_id) {
                        console.log(data.message, "uuid:", data.unique_id)
                        const uniqueId = data.unique_id
                        localStorage.setItem('dXVpZA==', uniqueId)
                    } else {
                        console.log('uuid already exists', data.unique_id)
                    }
                }
            } catch (error) {
                console.error('Message Error', error);
                errorMessage = '메시지 처리 중 오류가 발생했습니다.';
            }
        };

        ws.onclose = function(e) {
            console.log("Socket is closed. Reconnect will be attempted in 10 second.", e.reason);
            setTimeout(function() {
                reConnect(10000);
            });
        };
    }

    function reConnect(delay) {
        setTimeout(() => {
            console.log("Trying to reconnect...");
            connect();
        }, delay);
    }

    onMount(() => {
        connect();
    });

    onDestroy(() => {
        ws.close();
    });

    let scaleClass = '';

    async function handleButtonClick() {
        ws.send(JSON.stringify({"type": "click"}))
        console.log('button clicked')

        scaleClass = 'scale-up'
        setTimeout(() => {
            scaleClass = ''
        }, 250)
    }

    let imageClicked = false;

    function onMouseUp() {
        imageClicked = false;
    }

    if (unique_id === true) {
        newGuest = false
    } else {
        newGuest = true
    }

    if (storeData === "True") {
        newGuest = false
    } else {
        newGuest = true
    }

    function saveNick() {
        let nickname = document.getElementById('nickname').value;
        if (nickname) {
            newGuest = false
            nickname = JSON.stringify({"type": "nickname", "nickname": nickname})
            ws.send(nickname)

            localStorage.setItem('c3RvcmU=', "True")
            console.log("nickname is :",nickname)

            location.reload()
        } else {
            let errorDiv = document.getElementById('error')
            errorDiv.style.cssText =  "display: block; color: red; font-size: 10px;"
        }
    }
</script>

<main>
    <header>
        <div class="top" id="title">
            <a href="/">
                <img src="/static/고양이1.png" alt="none" draggable="false">
                <h1>잡캣</h1>
            </a>
        </div>

        <div class="top" id="info">
            <h1>{userName}</h1>
            <h2 class={scaleClass}>클릭수 : {userClicks}</h2>
        </div>

        <div class="top" id="top_right">
            <button style="height: fit-content; width: fit-content; font-size: 10px" on:click={function clear() {localStorage.clear()}}>RESET_LOACALSTORAGE</button>
        </div>
    </header>
    
    <figure>
        <button on:mousedown={handleButtonClick} on:mouseup={onMouseUp} on:mouseleave={onMouseUp}>
            {#if imageClicked}
                <img id="cat" src="/static/고양이.png" alt="none" draggable="false">
            {:else}
                <img id="cat" src="/static/고양이1.png" alt="none" draggable="false">
            {/if}
        </button>
    </figure>

    <footer>

    </footer>
</main>

<aside>
    <h2>현재 접속중인 사용자</h2>
    <ul class="user_list">
    {#each users as {name, clicks}}
        <li>{name} : <strong>{clicks}클릭</strong></li>
    {/each}
    </ul>
</aside>

{#if newGuest}
<sub>
    <div class="pop">
        <div class="pop_wrap">
            <h2>처음 오셨네요!</h2>
            <input id="nickname" type="text" placeholder="닉네임 입력">
            <div id="error" style="display: none;">닉네임을 입력해 주세요.</div>
            <div class="button_wrap">
                <button on:click={saveNick}>저장하기</button>
                <button on:click={() => newGuest = false}>익명으로<br>하기</button>
            </div>
            <div class="warnning">
                <h3>주의!</h3>
                <p>익명으로 진행하시면, 새로고침이나 다시 접속했을 때 기록이 저장되지 않습니다!</p>
                <p>(사이트 캐시를 초기화 하시면 기록 데이터가 소실될 수 있습니다.)</p>
            </div>
        </div>
    </div>
</sub>
{/if}

<style>
    main {
        height: fit-content;
        max-width: 100%;
    }

    header {
        height: 8vh;
        width: 100%;

        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    header .top {
        min-width: 200px;
    }

    header #title {
        height: 100%;
        width: fit-content;

        margin-left: 20px;
        margin-right: 20px;

        display: flex;
        justify-content: center;
        align-items: center;
    }

    header #title a {
        height: 100%;
        width: 100%;

        display:  flex;
        justify-content: center;
        align-items: center;

        text-decoration: none;
        color: black;
    }

    header #title a h1 {
        margin: 0;

        font-size: 60px;
        font-family: "Gamja Flower", sans-serif;
    }

    header #title img{
        height: 80px;
    }

    header #info {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }

    header #info h1, header #info h2 {
        margin: 0;
    }

    figure {
        height: 84vh;
        width: inherit;

        display: flex;
        justify-content: center;
        align-items: center;
    }

    figure button {
        height: 100%;
        width: 75%;

        background-color: transparent;
        border: none;
    }

    figure button #cat {
        transition: transform 0.15s ease;
        pointer-events: none;
    }

    figure button:active #cat {
        transform: scale(0.8);
    }

    footer {
        height: 6vh;
        width: 100%;
    }

    sub {
        height: 100%;
        width: 100%;

        top: 0;
        position: absolute;

        display: flex;
        justify-content: center;
        align-items: center;

        animation: darken 0.7s forwards;
    }

    @keyframes scale-up {
        0% { transform: scale(1); }
        50% { transform: scale(1.5); }
        100% { transform: scale(1); }
    }

    .scale-up {
        animation: scale-up 0.2s ease-in-out;
    }

    @keyframes darken {
    from {
        background-color: rgba(255, 255, 255, 0);
        opacity: 1;
    }
    to {
        background-color: rgba(80, 80, 80, 0.87);
        opacity: 1;
        }
    }

    .pop {
        height: 300px;
        width: 200px;

        padding: 10px;

        border: 2px solid black;
        border-radius: 20px;

        background-color: rgb(230, 230, 230);
    }

    .pop_wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    #nickname {
        width: 100%;

        border: 1px solid rgb(170, 170, 170);
        border-radius: 5px;
    }

    #error {
        width: 100%;

        margin-bottom: 10px;
    }

    .button_wrap {
        width: 100%;

        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }

    .button_wrap button {
        height: 50px;
        width: 100%;

        padding: 0;

        border: 1px solid rgb(170, 170, 170);
        border-radius: 5px;

        font-size: 15px;
        font-weight: 600;
    }

    .warnning {
        text-align: center;
    }

    .warnning p {
        margin: 0;
    }
</style>