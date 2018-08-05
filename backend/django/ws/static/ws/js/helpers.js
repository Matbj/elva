Array.prototype.contains = function ( needle ) {
   for (let i in this) {
      if (this[i] === needle) return true;
   }
   return false;
};
