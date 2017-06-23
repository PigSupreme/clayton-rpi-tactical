#!/usr/bin/env/ python
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

# namedtuple used for better message objects
from collections import namedtuple

# Experimental message logging
import logging

# Experimental: Using a heap for the message queue
import heapq

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
        if int(myID) < BaseEntity._min_new_ID:
            raise ValueError('Entity ID %d is already in use.' % myID)
        else:
            self._myID = myID
            BaseEntity._min_new_ID += 1
            self.postoffice = postoffice

    def get_id(self):
        """Returns the ID of this entity."""
        return self._myID

    def update(self):
        """Update method that will be called each step.

        Note
        ----
        This must be implemented by subclasses.
        """
        raise NotImplementedError(str(type(self))+" has undefined update().")

    def receive_msg(self,message):
        """Message handler; must be implemented my subclasses.

        Parameters
        ----------
        message: tuple
            A message constructed using the telegram() function.

        Note
        ----
        This must be implemented by subclasses.
        """
        raise NotImplementedError(str(type(self))+" has undefined receive_msg().")

class EntityManager(object):
    """Manager class for objects of type BaseEntity."""
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
            entity.manager = self
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
                logging.warn('%s.remove: Entity %s not in directory', self, entity)

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

        Note
        ----
        The order in which entities are called is arbitrary.
        """
        for entity in self._directory.values():
            entity.update()

    def start_all_fsms(self):
        """Starts the FSM for each entity that has one."""

        for entity in self._directory.values():
            try:
                entity.fsm.start()
            except AttributeError:
                logging.warn("Entity %s has no FSM, unable to start.", entity.name)

class EntityMessage(namedtuple('Message', 'DELAY, SEND_ID, RECV_ID, MSG_TYPE, EXTRA')):
    """An envelope/message for sending information between entities.

    This is called by the MessageDispatcher class and should not be used
    directly. To create the actual message, use MessageDispatcher.post_msg().
    
    TODO: Consider changing DELAY to some kind of timestamp.
    """

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
        self.message_q = [] # This will be a heap
        self.now = clock_now
        self.directory = ent_mgr

    def discharge(self,receiver,message):
        """Helper function for sending messages; internal use only."""
        logging.debug('PostOffice: Discharged message at time %d\n %s', self.now(), message)
        receiver.receive_msg(message)

    def post_msg(self,delay,send_id,rec_id,msg_type,extra=None):
        """Add a message to the queue for immediate or delayed dispatch.

        Parameters
        ----------
        delay: float
            Time (from now) at which to send the message. If zero/negative,
            the message will be dispatched immediately.
        send_id: int
            The ID of the BaseEntity sending the message.
        recv_id: int
            The ID of the BaseEntity that will receive the message.
        msg_type: int
            A tag that identifies the general type of message being sent.
        extra: anytype
            Optional information assumed to be handled by the recipient.
        """
        receiver = self.directory.get_entity_from_id(rec_id)
        if receiver:
            # Create the telegram
            message = EntityMessage(delay,send_id,rec_id,msg_type,extra)
            if delay <= 0:
                # Discharge immediately
                logging.debug('PostOffice: Received message for immediate delivery.')
                self.discharge(receiver,message)
            else:
                delivery_time = delay + self.now()
                logging.debug('PostOffice: Received delayed message at time %d, for delivery at time %d.\n %s',
                             self.now(), delivery_time, message)
                # Add delayed message to the delivery queue
                heapq.heappush(self.message_q, (delivery_time, message))

    def dispatch_delayed(self):
        """Dispatches messages from the delayed queue; internal use only."""
        # Dispatch messages until queue empty or next message in the future
        while len(self.message_q) > 0 and self.message_q[0][0] <= self.now():
            msg = heapq.heappop(self.message_q)[1]
            receiver = self.directory.get_entity_from_id(msg.RECV_ID)
            if receiver:
                self.discharge(receiver,msg)
