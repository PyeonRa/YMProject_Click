<script>
    import { onMount, onDestroy } from 'svelte';
    let users = []
    let usersRanking = []
    let errorMessage = '';
    let ws;
    $: newGuest = ''
    let userName = '';
    let userClicks = 0;
    let unique_id = localStorage.getItem('dXVpZA==')
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
                        unique_id = uniqueId
                    } else {
                        console.log('uuid already exists', data.unique_id)
                    }
                } else if (data.type === "ranking") {
                    usersRanking = data.users.map(user => ({ name: user.nickName, clicks: user.click }));
                    console.log(usersRanking)
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
        imageClicked = true;
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

    let asideButtonContent = '숨기기'
    let isAsideVisible = true

    function asideButton() {
        isAsideVisible = !isAsideVisible
        if (isAsideVisible) {
            asideButtonContent = '숨기기'
        } else {
            asideButtonContent = '펼치기'
        }
    }

    let slideRank = false

    function asideSlide(select) {
        if (select === 'rank') {
            slideRank = !slideRank
            console.log('yeyeyeyeye')
        }
    }

let update = true
</script>
{#if update}
<div class="update">
    <h1>업데이트중!</h1>
    <p>실시간 업데이트중...</p>
    <p>(업데이트 일시 중단.)</p>
</div>
{/if}

<main>
    <header>
        <div class="top" id="title">
            <a href="/">
                <img src="/static/고양이1.png" alt="none" draggable="false">
                <h1>잡캣</h1>
            </a>
        </div>

        <div class="top" id="info">
            <h1 title="{userName}">{userName}</h1>
            <h2 class={scaleClass} title="{userClicks}">클릭수 : {userClicks}</h2>
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

<div class="aside_wrap">
    <aside id="aside_left" style="left: {isAsideVisible ? '0' : '-280px'};">
        <h2>현재 접속중인 사용자</h2>
        <ol class="user_list">
        {#each users as {name, clicks}}
            <li><span>{name}</span> : <strong>{clicks}클릭</strong></li>
        {/each}
        </ol>
        <button class="aside_button" on:click={asideButton}>
            {#if isAsideVisible}
                <span class="material-symbols-outlined">
                    chevron_left
                </span>
            {:else}
                <span class="material-symbols-outlined">
                    chevron_right
                </span>
            {/if}
            {asideButtonContent}
        </button>
    </aside>

    <aside id="aside_right">
        <div class="aside_menu" id="rank">
            <button on:click={() => asideSlide('rank')}>
                <span class="material-symbols-outlined">
                    social_leaderboard
                </span>
            </button>
        </div>
    </aside>

    <div class="aside_right_slide" style="right: {slideRank ? '50px' : '-320px'}">
        <h2>역대 클릭 순위</h2>
        <ol>
            {#each usersRanking as {name, clicks}}
                <li><span>{name}</span> : <strong>{clicks}클릭</strong></li>
            {/each}
        </ol>
    </div>
</div>

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
    .update {
        height: 200px;
        width: 300px;

        top: 0;
        left: 15vw;
        position: absolute;

        display: flex;
        flex-direction: column;
        align-items: center;

        background-color: #8888889a;
        border: 2px solid black;
        border-radius: 10px;
    }

    .update h1{
        color: red;
    }

    main {
        height: 100%;
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

        display: flex;
        align-items: center;

        user-select: none;
    }

    header #title a {
        height: 100%;
        width: 100%;

        margin-left: 10px;

        display:  flex;
        justify-content: start;
        align-items: center;

        text-decoration: none;
        color: black;
    }

    header #title a h1 {
        margin: 0;

        font-size: 6vh;
        font-family: "Gamja Flower", sans-serif;

        white-space: nowrap;
    }

    header #title img{
        height: 9vh;
    }

    header #info {
        width: 100%;

        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 5px;
    }

    header #info h1, header #info h2 {
        width: 35%;

        margin: 0;

        user-select: none;

        text-align: center;
        white-space: nowrap;
    }

    header #info h1 {
        font-size: 3vh;

        overflow: hidden;
        text-overflow: ellipsis;
    }

    header #info h2 {
        font-size: 2vh;
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
        width: 85%;

        background-color: transparent;
        border: none;

        cursor: pointer;
        user-select: none;
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

    .aside_wrap {
        height: 100%;
        width: 100%;

        top: 0;
        left: 0;
        position: absolute;

        display: flex;
        justify-content: space-between;
        align-items: center;

        overflow-x: hidden;

        pointer-events: none;
        user-select: none;
    }

    #aside_left {
        height: 76vh;
        width: 300px;

        position: relative;

        background-color: rgb(210, 210, 210);
        border-top: 3px solid black;
        border-right: 3px solid black;
        border-bottom: 3px solid black;
        border-radius: 0 10px 10px 0;

        transition: left 0.5s ease-in-out;

        pointer-events: auto;
    }

    #aside_left::-webkit-scrollbar {
        width: 10px;
    }

    #aside_left::-webkit-scrollbar-thumb {
        background: #888;

        border-radius: 5px;
    }

    #aside_left h2{
        font-size: 18px;
        text-align: center;
    }

    ol {
        padding-left: 50px;
        padding-right: 20px;
    }

    ol li {
        width: 100%;

        padding-bottom: 5px;

        font-size: 15px;
    }

    ol li::marker {
        font-size: 20px;
        font-weight: 700;
    }

    ol li span{
        max-width: 100%;

        top: 5px;
        position: relative;

        display: inline-block;

        font-size: 18px;
        font-weight: 600;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }

    #aside_left button {
        height: 80px;
        width: 25px;

        margin: 0;
        padding: 0 0 0 24px;

        top: 2vh;
        right: -30px;
        position: absolute;
        z-index: 1;

        font-size: 12px;
        font-weight: 800;
        writing-mode: vertical-rl;

        background: none;
        border-left: none;
        border-top: 3px solid black;
        border-right: 3px solid black;
        border-bottom: 3px solid black;
        border-top-right-radius: 5px;
        border-top-left-radius: 0;
        border-bottom-right-radius: 5px;
        border-bottom-left-radius: 0;

        cursor: pointer;
    }

    #aside_left button span {
        height: 20px;
        width: fit-content;

        margin: 0;
        padding: 0;

        writing-mode: horizontal-tb;
    }

    #aside_left button:active {
        background-color: rgb(200, 200, 200);
    }

    #aside_right {
        height: 76vh;
        width: 18vw;

        position: relative;

        display: flex;
        flex-direction: column;
        align-items: end;
        justify-content: center;

        pointer-events: auto;
    }

    #aside_right #rank button {
        height: fit-content;
        width: fit-content;

        border: none;

        background: none;

        cursor: pointer;
    }

    #aside_right #rank button span {
        font-size: 40px;
    }

    .aside_right_slide {
        height: 76vh;
        width: 300px;

        position: absolute;

        background-color: rgb(210, 210, 210);
        border-top: 3px solid black;
        border-left: 3px solid black;
        border-bottom: 3px solid black;
        border-right: 3px solid black;
        border-radius: 10px 10px 10px 10px;

        overflow: scroll;
        overflow-x: hidden;

        transition: right 0.5s ease-in-out;

        pointer-events: auto;
        user-select: none;
    }

    .aside_right_slide::-webkit-scrollbar {
        width: 10px;
    }

    .aside_right_slide::-webkit-scrollbar-thumb {
        background: #888;

        border-radius: 5px;
    }

    .aside_right_slide h2 {
        font-size: 18px;
        text-align: center;
    }

    sub {
        height: 100%;
        width: 100%;

        top: 0;
        position: absolute;
        z-index: 10;

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
        height: 320px;
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