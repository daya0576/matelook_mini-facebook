/**
 * Created by henry on 20/10/16.
 */
function show_comments(obj) {
    alert($(obj).next(".comments"));
    // $(obj).
    $(obj).parents(".box_top").next().show();
}