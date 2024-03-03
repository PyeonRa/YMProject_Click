<script>
    import { onMount, onDestroy } from 'svelte';
    let users = [];
    let errorMessage = '';
    let ws;
    $: newGuest = true
    const unique_id = localStorage.getItem('dXVpZA==')

    function connect() {
        const hostname = window.location.hostname;
        const serverAddress = hostname === 'yullmu.com'
            ? 'ws://yullmu.com/ws'
            : 'ws://127.0.0.1:4001/ws';

        ws = new WebSocket(serverAddress);

        ws.onopen = () => {
            console.log('Connected');
            errorMessage = '';


            ws.send(JSON.stringify({"type": "uuid", "uuid": unique_id}))
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error', error);
            errorMessage = 'WebSocket 연결에 실패했습니다.';
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "users") {
                    users = data.users.map(user => ({ name: user.nickName, clicks: user.click }));
                    console.log(data)
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

    function handleButtonClick() {
        ws.send(JSON.stringify({"type": "click"}));
        console.log('button clicked')
    }


    if (unique_id === true) {
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
            console.log("nickname is :",nickname)
        } else {
            let errorDiv = document.getElementById('error')
            errorDiv.style.cssText =  "display: block; color: red; font-size: 10px;"
        }
    }
</script>

<main>
    <div class="top_blank"><a href="/"><img id="title_cat" src="/static/cat.png" alt="none" draggable="false">잡캣</a></div>
    <header>

    </header>
    <div class="top_blank"><button style="height: 100px; width: fit-content; font-size: 30px" on:click={function clear() {localStorage.clear()}}>RESET_LOACALSTORAGE</button></div>

    <aside>
        <h2>현재 접속중인 사용자</h2>
        <ul class="user_list">
        {#each users as {name, clicks}}
            <li>{name} : <strong>{clicks}클릭</strong></li>
        {/each}
        </ul>
    </aside>

    <figure>
        <button on:click={handleButtonClick}>
            <img id="cat" src="/static/cat.png" alt="none" draggable="false">
        </button>
    </figure>

    <aside>

    </aside>

    <div class="bottom_blank"></div>
    <footer>

    </footer>
    <div class="bottom_blank"></div>
</main>

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
            </div>
        </div>
    </div>
</sub>
{/if}

<style>
    main {
        height: 100vh;
        max-width: 100vw;

        display: grid;
        grid-template-columns: 1fr 5fr 1fr;
        grid-template-rows: 1fr 10fr 1fr;
        grid-gap: 20px;
        grid-template-areas: 
            "1_div header 2_div"
            "left_aside figure right_aside"
            "3_div footer 4_div";
    }

    header {
        grid-area: header;

        width: 100%;
        
        background-color: black;
    }

    .top_blank:nth-of-type(1) {
        grid-area: 1_div;

        padding-left: 1vw;

        display: flex;
        justify-content: start;
        align-items: center;

        font-size: 80px;
        font-family: "Gamja Flower", sans-serif;
    }

    .top_blank:nth-of-type(1) a {
        display: flex;
        justify-content: center;
        align-items: center;

        color: black;
        text-decoration: none;
    }

    #title_cat {
        height: 5vh;
    }

    .top_blank:nth-of-type(2) {
        grid-area: 2_div;

        background-color: white;
    }

    aside:first-of-type {
        grid-area: left_aside;

        padding-left: 1vw;
    }

    aside:last-of-type {
        grid-area: right_aside;
    }

    .user_list {
        display: flex;
        flex-direction: column;
        align-items: start;
        justify-content: start;
        gap: 10px;
    }

    aside, .user_list{
        max-width: 100%;

        white-space: nowrap;
        text-overflow: ellipsis;
    }

    .user_list strong {
        max-width: 100%;
    }
    
    figure {
        grid-area: figure;

        background-color: none;
    }

    figure button {
        height: 100%;
        width: 100%;

        background: none;
        border: none;

        cursor: pointer;
        overflow: hidden;
    }

    figure button:active #cat {
        transform: scale(0.7);
    }

    #cat {
        height: 75%;

        transition: transform 0.15s ease;
    }

    footer {
        grid-area: footer;

        background-color: black;
    }

    .bottom_blank:nth-of-type(3) {
        grid-area: 3_div;

        background-color: white;
    }

    .bottom_blank:nth-of-type(4) {
        grid-area: 4_div;

        background-color: white;
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
</style>