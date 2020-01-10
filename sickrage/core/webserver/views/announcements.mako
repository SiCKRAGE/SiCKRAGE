% for announcement in announcements:
    <div class="announcement-container">
        <div class="card card-block text-white bg-dark m-1 shadow">
            <h4>${announcement['title']}</h4>
            <img src="${announcement['image']}"/>
            <div class="date">${announcement['date']}</div>
            <div class="description">${announcement['description']}</div>
        </div>
    </div>
% endfor