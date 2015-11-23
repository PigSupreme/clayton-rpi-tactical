# -*- coding: utf-8 -*-
"""Module for defining managing game-type entities.

Use the BaseEntity class for agents that need a unique ID as well as
periodic updating and messaging functionality. The EntityManager class
provides a simple interface for automatic management.

Messages are sent via an instance of the MessageDispatcher class. This
works with an EntityManager in order to serve as a kind of post office.
Both immediate and delayed messages are possible; see the class description.
"""

# for python3 compat
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

class BaseEntity(object):
    """Abstract Base Class for objects with an ID, update, and messaging.
    
    Parameters
    ----------
    myID: int
        The unique ID assigned to this entity.
    postoffice: MessageDispatcher
        Where this entity will send its messages.
        
    Raises
    ------
    ValueError
        If the requested ID is invalid.
    
    Notes
    -----      
    Because of how messaging is implemented, each entity needs a unique ID.
    We use a private class variable to make sure that ID's are not repeated.
    Since ID's aren't recycled, we can't accidentally send a message or
    otherwise refer to an entity that is no longer valid.
    
    """
    _min_new_ID = 1 
    
    def __init__(self, myID, postoffice):
        if myID < BaseEntity._min_new_ID:
            raise ValueError('Entity ID %d is already in use.' % myID)
        else:    
            self._myID = myID
            BaseEntity._min_new_ID += 1
            self.postoffice = postoffice
            
    def get_id(self):
        """Returns the ID of this entity."""
        return self._myID
            
    def update(self):
        """Update method that will be called each step
        This must be implemented by subclasses.
        """
        raise NotImplementedError(str(type(self))+" has undefined update().")
        
    def receive_msg(self,message):
        """Message handler; must be implemented my subclasses.
        
        Parameters
        ----------
        message: tuple
            A message constructed using the telegram() function.
        """
        raise NotImplementedError(str(type(self))+" has undefined receive(message).")

class EntityManager(object):
    """Manager class for objects of type BaseEntity"""
    def __init__(self):
        self._directory = dict()
    
    def register(self, entity):
        """Add an instance of BaseEntity to this manager.

        Parameters
        ----------
        entity: BaseEntity
            An entity that has been instantiated outside of this class.
        """
        if isinstance(entity, BaseEntity):
            self._directory[entity.get_id()] = entity
        else:
            raise TypeError("Object %s type is not derived from BaseEntity" % self)
    
    def remove(self, entity):
        """Remove an instance of BaseEntity from this manager.
        
        Notes
        -----
        Since BaseEntity's are instantiated/deleted outside of this class,
        removing only affects this manager's behavior. This function checks
        whether entity has the correct type, so deleting entity before
        removing it from the manager shouldn't be an issue.
        """
        if isinstance(entity, BaseEntity):
            try:
                del self._directory[entity.get_id()]
            except KeyError:
                print('WARNING: Entity %s not in directory' % str(entity))
                
    def get_entity_from_id(self,ent_id):
        """Returns an entity object from its ID.
        
        Returns
        -------
        BaseEntity
            The entity corresponding to ent_id.
            If this ID isn't registered, returns None.
        """
        try:
            return self._directory[ent_id]
        except KeyError:
            return None
            
    def update(self):
        """Calls the update() method of all registered entities.
        
        Note: The order in which entities are called in not known.
        """        
        for entity in self._directory.values():
            entity.update()
            
    def start_all_fsms(self):
        """Starts the FSM for each entity that has one."""
        
        for entity in self._directory.values():
            try:
                entity.fsm.start()
            except AttributeError:
                print("Note: Entity %s has no FSM: ignoring" % entity.name)
                

# Fake enumeration of telegram info fields
DELAY, SEND_ID, RECV_ID, MSG_TYPE, EXTRA = range(5)

def _telegram(delay,send_id,rec_id,msg_type,extra_info=None):
    """Helper function used by MessageDispatcher to generate messages.
    
    Note
    ----
    
    This function should not be called directly; you should instead use the
    MessageDispatcher.post_msg() method. The original C++ code used struct
    to define telegrams, so this function served a greater purpose. We might
    be able to either eliminate this function entirely, or rewrite things so
    that telegram is a class, but it'll do for now.
    """
    return (delay,send_id,rec_id,msg_type,extra_info)

class MessageDispatcher(object):
    """Class for posting/handling messages between entities.

    Parameters
    ----------

    clock_now: function()
        A function that returns a numerical value. This is used to represent
        the current time to control delivery of delayed messages.
    ent_mgr: EntityManager
        Used by this class to lookup an entity, given its ID.    
    """
    def __init__(self, clock_now, ent_mgr):
        self.queue = dict() # Better way to implement this??
        self.now = clock_now
        self.directory = ent_mgr
    
    def discharge(self,receiver,message):
        """Passes a message to a given recipient."""
        #print("Now discharging...")
        receiver.receive_msg(message)
    
    def post_msg(self,delay,send_id,rec_id,msg_type,extra=None):
        """Add a message to the queue for immediate or delayed dispatch."""
        receiver = self.directory.get_entity_from_id(rec_id)
        if receiver:
            # Create the telegram
            message = _telegram(delay,send_id,rec_id,msg_type,extra)
            if delay <= 0:
                # Discharge immediately
                self.discharge(receiver,message)
            else:
                # Add delayed message to queue here
                delivery_time = delay + self.now()
                # print("POST OFFICE : At time %d, posted delayed message for time %d." % (current_time, delivery_time))
                try:
                    self.queue[delivery_time].append(message)
                except KeyError:
                    self.queue[delivery_time] = [message]
    
    def dispatch_delayed(self):
        """Dispatches messages from the delayed queue."""
        now = self.now()
        # Message queue is keyed by desired delievery time; sort it first
        for t in sorted(self.queue.keys()):
            # Since we sort before discharging, break if we hit the future            
            if t > now:
                break
            
            # Pop and dispatch all messages at this time until none remain
            msglist = self.queue[t]
            while msglist != []:
                msg = msglist.pop(0) # FIFO for each point in time
                receiver = self.directory.get_entity_from_id(msg[RECV_ID])
                if receiver:
                    self.discharge(receiver,msg)
            
            # We can delete this time key if needed
            del self.queue[t]
